import pandas as pd


def compare(path: str):
    stk_frame = pd.read_csv(path + "/stk.csv")
    fs_frame = pd.read_csv(path + "/florasat.csv")

    stk_frame.loc[:, "Lat"] = stk_frame.loc[:, "Lat"].add(90)
    fs_frame.loc[:, "Lat"] = fs_frame.loc[:, "Lat"].add(90)

    stk_frame.loc[:, "Lon"] = stk_frame.loc[:, "Lon"].mod(180)
    fs_frame.loc[:, "Lon"] = fs_frame.loc[:, "Lon"].mod(180)

    new_frame = pd.DataFrame()

    new_frame.loc[:, "STK-Lat"] = stk_frame.loc[:, "Lat"]
    new_frame.loc[:, "STK-Lon"] = stk_frame.loc[:, "Lon"]
    new_frame.loc[:, "FLoRa-Lat"] = fs_frame.loc[:, "Lat"]
    new_frame.loc[:, "FLoRa-Lon"] = fs_frame.loc[:, "Lon"]
    # new_frame.loc[:,"Lat-Dev. [%]"] = ((stk_frame.Lat - fs_frame.Lat) / stk_frame.Lat * 100).abs()
    # new_frame.loc[:,"Lon-Dev. [%]"] = ((stk_frame.Lon - fs_frame.Lon) / stk_frame.Lon * 100).abs()
    new_frame.loc[:, "Lat-Dev. [%]"] = (((stk_frame.Lat / fs_frame.Lat) - 1) * 100).abs()
    new_frame.loc[:, "Lon-Dev. [%]"] = (((stk_frame.Lon / fs_frame.Lon) - 1) * 100).abs()
    new_frame = new_frame.round(2)
    new_frame.to_latex("results/" + path + ".tex")
    print(new_frame)

    print("Lat-Std.dev", new_frame.loc[:, "Lat-Dev. [%]"].mean().round(2))
    print("Lon-Std.dev", new_frame.loc[:, "Lon-Dev. [%]"].mean().round(2))


compare("iridium")
