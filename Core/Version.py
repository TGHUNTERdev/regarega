appname  = "TGHReger"
major    = 1
minor    = 6
micro    = 2
stage    = 5
name     = ""
snapshot = "UPD"

version = f"{major}.{minor}.{micro}"
if stage is not None:
    version += f".{stage}"
if name:
    version += " "+name
if snapshot:
    version += " "+snapshot
