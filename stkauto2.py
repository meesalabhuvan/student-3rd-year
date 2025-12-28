import csv
import os
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import *

class STKAutomation:

    def __init__(self, visible=True):
        print("[INFO] Launching STK...")
        self.app = STKDesktop.StartApplication(visible=visible)
        self.root = self.app.Root
        print("[OK] STK Launched.")

    def new_scenario(self, name, start="Today", stop="+250hr"):
        print(f"[INFO] Creating scenario: {name}")
        self.root.NewScenario(name)
        self.scenario = self.root.CurrentScenario
        self.scenario.SetTimePeriod(start, stop)
        self.root.Rewind()
        print("[OK] Scenario created.")

    def add_satellite(self, name):
        print(f"[INFO] Adding satellite: {name}")
        sat = self.scenario.Children.New(AgESTKObjectType.eSatellite, name)
        return sat

    def add_target(self, name, lat, lon, alt=0):
        print(f"[INFO] Adding target: {name}")
        tgt = self.scenario.Children.New(AgESTKObjectType.eTarget, name)
        tgt.Position.AssignGeodetic(lat, lon, alt)
        return tgt

    def set_simple_orbit(self, sat, sma=7000000, ecc=0, inc=98, aop=0, ta=0):
        print("[INFO] Setting orbit...")
        cmd = (f'SetState {sat.Path} Classical TwoBody '
               f'"{self.scenario.StartTime}" "{self.scenario.StopTime}" 60 '
               f'ICRF "{self.scenario.StartTime}" '
               f'{sma} {ecc} {inc} 0 {aop} {ta}')
        self.root.ExecuteCommand(cmd)
        print("[OK] Orbit applied.")

    def get_access(self, sat, tgt):
        print("[INFO] Computing access...")
        access = sat.GetAccessToObject(tgt)
        access.ComputeAccess()

        print("[OK] Access computed.")

        provider = access.DataProviders.Item("Access Intervals by Time")

        

        result = provider.Exec() 
        print("[OK] Access computed.")
        return result 
    

    def save_access_csv(self, result, file_path):
        print("[INFO] Extracting access data...")
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)


        ds = result.DataSets

        start_times = ds.Item(0).GetValues()
        stop_times = ds.Item(1).GetValues()
        durations  = ds.Item(2).GetValues()

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Start Time", "Stop Time", "Duration"])

            for i in range(len(start_times)):
                writer.writerow([start_times[i], stop_times[i], durations[i]])

        print(f"[OK] Saved access report: {file_path}")
        
#main function

if __name__ == "__main__":
    print("\n===== STK AUTOMATION STARTED =====\n")
    stk = STKAutomation(visible=True)
    stk.new_scenario("Mission1")
    sat = stk.add_satellite("MySat")
    tgt = stk.add_target("HYD", 17.385, 78.486)
    stk.set_simple_orbit(sat)
    access = stk.get_access(sat, tgt)
    stk.save_access_csv(access, "C:/STKReports/MySat_Access1.csv")

    print("\n===== STK AUTOMATION COMPLETED =====\n")

