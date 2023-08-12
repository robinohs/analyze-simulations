use std::{
    fs::{self, File},
    io::BufReader,
};

use itertools::Itertools;
use map_3d::{deg2rad, geodetic2ecef};
use pyo3::prelude::*;
use rmp_serde::Serializer;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct Record {
    pid: u32,
    #[serde(rename = "type")]
    typ: char,
    id: u32,
    lat: f32,
    lon: f32,
    alt: u16,
}

#[pyclass(module = "hop", get_all)]
#[derive(Clone, Serialize, Deserialize, Debug)]
struct Hop {
    #[serde(rename = "type")]
    typ: char,
    id: u32,
    lat: f32,
    lon: f32,
    alt: u16,
}

#[pymethods]
impl Hop {
    fn to_ecef(&self) -> (f64, f64, f64) {
        geodetic2ecef(
            deg2rad(self.lat as f64),
            deg2rad(self.lon as f64),
            ((self.alt as u32) * 1000) as f64,
            map_3d::Ellipsoid::WGS84,
        )
    }

    fn distance(&self, other: &Self) -> f64 {
        let (x1, y1, z1) = self.to_ecef();
        let (x2, y2, z2) = other.to_ecef();
        ((x2 - x1).powi(2) + (y2 - y1).powi(2) + (z2 - z1).powi(2)).sqrt() / 1000.0
    }
}

#[pyclass(module = "route", get_all)]
#[derive(Clone, Serialize, Deserialize, Debug)]
struct Route {
    pid: u32,
    length: u32,
    hops: Vec<Hop>,
}

impl Route {
    fn new(pid: u32, hops: Vec<Hop>) -> Self {
        Route {
            pid,
            length: calculate_distance(&hops),
            hops,
        }
    }
}

#[pyfunction]
fn load_routes(read_path: String) -> PyResult<Vec<Route>> {
    let data = fs::read(read_path)?;
    let res: Vec<Route> = rmp_serde::from_slice(&data).expect("Unable to parse");
    Ok(res)
}

#[pyfunction]
fn process_routes(read_path: String, write_path: String, write_file: String) -> PyResult<()> {
    let file = File::open(read_path)?;
    let reader = BufReader::new(file);
    let mut rdr = csv::Reader::from_reader(reader);
    let mut current_pid;
    let mut routes = vec![];
    let mut hops = vec![];
    let mut iter = rdr.deserialize();

    // process first
    let first: Record = iter.next().unwrap().unwrap();
    current_pid = first.pid;
    let hop = Hop {
        typ: first.typ,
        id: first.id,
        lat: first.lat,
        lon: first.lon,
        alt: first.alt,
    };
    hops.push(hop);
    // process next
    for result in iter {
        // Notice that we need to provide a type hint for automatic
        // deserialization.
        let record: Record = result.unwrap();
        let pid = record.pid;
        if pid != current_pid {
            let route = Route::new(current_pid, hops);
            routes.push(route);
            current_pid = pid;
            hops = vec![];
        }
        let hop = Hop {
            typ: record.typ,
            id: record.id,
            lat: record.lat,
            lon: record.lon,
            alt: record.alt,
        };
        hops.push(hop);
    }

    if !hops.is_empty() {
        // process last
        let route = Route::new(current_pid, hops);
        routes.push(route);
    }

    let mut buf = Vec::new();
    routes.serialize(&mut Serializer::new(&mut buf)).unwrap();

    fs::create_dir_all(write_path)?;

    fs::write(write_file, buf)?;

    Ok(())
}

fn calculate_distance(hops: &Vec<Hop>) -> u32 {
    hops.iter()
        .tuple_windows()
        .fold(0.0, |acc, (a, b)| acc + a.distance(b))
        .round() as u32
}

/// A Python module implemented in Rust.
#[pymodule]
fn florasat_statistics(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Hop>()?;
    m.add_class::<Route>()?;
    m.add_function(wrap_pyfunction!(load_routes, m)?)?;
    m.add_function(wrap_pyfunction!(process_routes, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::{Hop, Route};

    #[test]
    fn test_calc_distance() {
        let test_hops = vec![
            Hop {
                id: 2,
                typ: 'G',
                lat: 22.5,
                lon: 11.4,
                alt: 0,
            },
            Hop {
                id: 55,
                typ: 'S',
                lat: 25.5,
                lon: 41.4,
                alt: 666,
            },
            Hop {
                id: 56,
                typ: 'S',
                lat: 33.5,
                lon: 40.4,
                alt: 664,
            },
            Hop {
                id: 4,
                typ: 'G',
                lat: 42.5,
                lon: 41.4,
                alt: 0,
            },
        ];
        let route = Route::new(22, test_hops);
        println!("route: {:?}", route);
    }
}
