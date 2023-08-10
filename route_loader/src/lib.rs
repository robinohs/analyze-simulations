use std::{
    fs::{self, File},
    io::{BufReader, Cursor},
};

use pyo3::prelude::*;
use rmp_serde::{Deserializer, Serializer};
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

#[derive(Serialize, Deserialize, Debug)]
struct Hop {
    #[serde(rename = "type")]
    typ: char,
    id: u32,
    lat: f32,
    lon: f32,
    alt: u16,
}

#[derive(Serialize, Deserialize, Debug)]
struct Route {
    pid: u32,
    hops: Vec<Hop>,
}

// #[pyfunction]
// fn load_routes(read_path: String) -> PyResult<Vec<Route>> {
//     let data = fs::read_to_string(read_path)?;
//     let res: Vec<Route> = serde_json::from_str(&data).expect("Unable to parse");
//     Ok(res)
// }

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
            let route = Route { pid: current_pid, hops };
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
        let route = Route {
            pid: current_pid,
            hops,
        };
        routes.push(route);
    }

    let mut buf = Vec::new();
    routes.serialize(&mut Serializer::new(&mut buf)).unwrap();

    fs::create_dir_all(write_path)?;

    fs::write(write_file, buf)?;

    Ok(())
}

/// A Python module implemented in Rust.
#[pymodule]
fn route_loader(_py: Python, m: &PyModule) -> PyResult<()> {
    // m.add_class::<Hop>()?;
    // m.add_class::<Route>()?;
    // m.add_function(wrap_pyfunction!(load_routes, m)?)?;
    m.add_function(wrap_pyfunction!(process_routes, m)?)?;
    Ok(())
}
