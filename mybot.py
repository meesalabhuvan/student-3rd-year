"""
Simple STK + Gemini CLI app (no Telegram)
-----------------------------------------

What this script does
---------------------
- Asks you in the terminal to describe an STK scenario.
- Sends that description to Gemini 2.5 Flash.
- Gemini returns Python code that should:
    * Use or simulate STK
    * Generate reports/screenshots (CSV / PNG) in a temp folder
- The script runs that generated Python with an STK‑capable interpreter.
- Finally, it lists the generated files and shows truncated output.


Environment variables
---------------------
- GOOGLE_API_KEY      : Your Google Gemini API key
- GOOGLE_GEMINI_MODEL : (optional) Model name, default: "gemini-2.5-flash"
- STK_PYTHON_CMD      : Path to Python that can run STK
                        (e.g. r"C:\\Python314\\python.exe")
"""

import os
import tempfile
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from google import genai  # pip install google-genai


# ----------------------------
# Basic configuration
# ----------------------------

# Gemini configuration
GOOGLE_API_KEY = os.getenv("AIzaSyAbICds9qo1S6cofkXw_zvMOQjwi7NudX", "AIzaSyAbICds9qo1S6cofkXw_zvMOQjwi7NudXY")
GOOGLE_GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.5-flash")

# Python interpreter that can run STK scripts
STK_PYTHON_CMD = os.getenv("STK_PYTHON_CMD", r"C:\Python314\python.exe")

# Thread pool for running blocking STK jobs (kept for possible future expansion)
WORKER_POOL = ThreadPoolExecutor(max_workers=2)

# Logging (prints information to console)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_stk_cli")


# ----------------------------
# Helper functions
# ----------------------------

def ensure_config_ok() -> None:
    """Check that required environment variables are set."""
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set. Set it in your environment.")
    if not STK_PYTHON_CMD:
        raise RuntimeError("STK_PYTHON_CMD is not set. Set it in your environment.")


def build_gemini_prompt(user_text: str) -> str:
    """
    Build a comprehensive instruction for Gemini to generate advanced STK automation code.
    """
    return f"""
You are an expert Python developer using AGI STK (Systems Tool Kit) v12+.
The user will describe a complex scenario in natural language. Your job is to create a complete,
production-ready STK automation script that handles ALL aspects mentioned.

CRITICAL: You MUST use the STKAutomation class pattern shown below. Expand it with additional
methods as needed for the user's scenario (sensors, transmitters, link budgets, coverage, etc.).

REQUIRED BASE CLASS STRUCTURE:

import csv
import os
from agi.stk12.stkdesktop import STKDesktop
from agi.stk12.stkobjects import *

class STKAutomation:
    def __init__(self, visible=True):
        print("[INFO] Launching STK...")
        try:
            self.app = STKDesktop.StartApplication(visible=visible)
            self.root = self.app.Root
            print("[OK] STK Launched.")
        except Exception as e:
            print(f"[ERROR] Failed to launch STK: {{e}}")
            raise

    def new_scenario(self, name, start="Today", stop="+250hr"):
        print(f"[INFO] Creating scenario: {{name}}")
        self.root.NewScenario(name)
        self.scenario = self.root.CurrentScenario
        self.scenario.SetTimePeriod(start, stop)
        self.root.Rewind()
        print("[OK] Scenario created.")

    def add_satellite(self, name):
        print(f"[INFO] Adding satellite: {{name}}")
        sat = self.scenario.Children.New(AgESTKObjectType.eSatellite, name)
        return sat

    def add_aircraft(self, name):
        print(f"[INFO] Adding aircraft: {{name}}")
        ac = self.scenario.Children.New(AgESTKObjectType.eAircraft, name)
        return ac

    def add_facility(self, name, lat, lon, alt=0):
        print(f"[INFO] Adding facility: {{name}}")
        fac = self.scenario.Children.New(AgESTKObjectType.eFacility, name)
        fac.Position.AssignGeodetic(lat, lon, alt)
        return fac

    def add_target(self, name, lat, lon, alt=0):
        print(f"[INFO] Adding target: {{name}}")
        tgt = self.scenario.Children.New(AgESTKObjectType.eTarget, name)
        tgt.Position.AssignGeodetic(lat, lon, alt)
        return tgt

    def add_place(self, name, lat, lon, alt=0):
        print(f"[INFO] Adding place: {{name}}")
        place = self.scenario.Children.New(AgESTKObjectType.ePlace, name)
        place.Position.AssignGeodetic(lat, lon, alt)
        return place

    def set_simple_orbit(self, sat, sma=7000000, ecc=0, inc=98, aop=0, ta=0):
        print("[INFO] Setting orbit...")
        cmd = (f'SetState {{sat.Path}} Classical TwoBody '
               f'\"{{self.scenario.StartTime}}\" \"{{self.scenario.StopTime}}\" 60 '
               f'ICRF \"{{self.scenario.StartTime}}\" '
               f'{{sma}} {{ecc}} {{inc}} 0 {{aop}} {{ta}}')
        self.root.ExecuteCommand(cmd)
        print("[OK] Orbit applied.")

    def set_geo_orbit(self, sat, longitude_deg):
        print(f"[INFO] Setting GEO orbit at {{longitude_deg}} deg...")
        cmd = f'SetState {{sat.Path}} Geosynchronous \"{{self.scenario.StartTime}}\" \"{{self.scenario.StopTime}}\" 60 ICRF \"{{self.scenario.StartTime}}\" {{longitude_deg}}'
        self.root.ExecuteCommand(cmd)
        print("[OK] GEO orbit applied.")

    def add_sensor(self, parent_obj, sensor_name, cone_half_angle_deg=45):
        print(f"[INFO] Adding sensor {{sensor_name}} to {{parent_obj.InstanceName}}...")
        sensor = parent_obj.Children.New(AgESTKObjectType.eSensor, sensor_name)
        sensor.CommonTasks.SetPatternSimpleConic(cone_half_angle_deg, 0)
        print("[OK] Sensor added.")
        return sensor

    def add_transmitter(self, parent_obj, tx_name, frequency_mhz=2400, power_dbm=30):
        print(f"[INFO] Adding transmitter {{tx_name}} to {{parent_obj.InstanceName}}...")
        tx = parent_obj.Children.New(AgESTKObjectType.eTransmitter, tx_name)
        tx.Model.Frequency = frequency_mhz
        tx.Model.PowerEIRP = power_dbm
        print("[OK] Transmitter added.")
        return tx

    def add_receiver(self, parent_obj, rx_name, frequency_mhz=2400):
        print(f"[INFO] Adding receiver {{rx_name}} to {{parent_obj.InstanceName}}...")
        rx = parent_obj.Children.New(AgESTKObjectType.eReceiver, rx_name)
        rx.Model.Frequency = frequency_mhz
        print("[OK] Receiver added.")
        return rx

    def compute_access(self, from_obj, to_obj):
        print(f"[INFO] Computing access from {{from_obj.InstanceName}} to {{to_obj.InstanceName}}...")
        access = from_obj.GetAccessToObject(to_obj)
        access.ComputeAccess()
        print("[OK] Access computed.")
        return access

    def get_access_intervals(self, access):
        provider = access.DataProviders.Item("Access Intervals by Time")
        result = provider.Exec()
        return result

    def get_aer_data(self, access):
        print("[INFO] Getting AER (Azimuth, Elevation, Range) data...")
        provider = access.DataProviders.Item("AER Data")
        provider.PreData.SetTimeStep(60)
        result = provider.Exec()
        print("[OK] AER data retrieved.")
        return result

    def compute_link_budget(self, tx_obj, rx_obj):
        print("[INFO] Computing link budget...")
        link = tx_obj.GetLinkToObject(rx_obj)
        link.ComputeAccess()
        provider = link.DataProviders.Item("Link Budget")
        result = provider.Exec()
        print("[OK] Link budget computed.")
        return result

    def compute_coverage(self, sensor, region_name="CoverageRegion"):
        print("[INFO] Computing coverage...")
        cov = self.scenario.Children.New(AgESTKObjectType.eCoverageDefinition, region_name)
        cov.AssetList.Add(sensor.Path)
        cov.Grid.BoundsType = AgECoverageBoundsType.eBoundsCustomRegions
        cov.Grid.BoundsCustomRegions.Add(region_name)
        cov.ComputeCoverage()
        print("[OK] Coverage computed.")
        return cov

    def save_access_csv(self, result, file_path):
        print(f"[INFO] Saving access report to {{file_path}}...")
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        ds = result.DataSets
        start_times = ds.Item(0).GetValues()
        stop_times = ds.Item(1).GetValues()
        durations = ds.Item(2).GetValues()
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Start Time", "Stop Time", "Duration (sec)"])
            for i in range(len(start_times)):
                writer.writerow([start_times[i], stop_times[i], durations[i]])
        print(f"[OK] Saved: {{file_path}}")

    def save_aer_csv(self, result, file_path):
        print(f"[INFO] Saving AER report to {{file_path}}...")
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        ds = result.DataSets
        times = ds.Item(0).GetValues()
        azimuths = ds.Item(1).GetValues()
        elevations = ds.Item(2).GetValues()
        ranges = ds.Item(3).GetValues()
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Azimuth (deg)", "Elevation (deg)", "Range (km)"])
            for i in range(len(times)):
                writer.writerow([times[i], azimuths[i], elevations[i], ranges[i]])
        print(f"[OK] Saved: {{file_path}}")

    def save_link_budget_csv(self, result, file_path):
        print(f"[INFO] Saving link budget to {{file_path}}...")
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        ds = result.DataSets
        times = ds.Item(0).GetValues()
        eirp = ds.Item(1).GetValues()
        path_loss = ds.Item(2).GetValues()
        received_power = ds.Item(3).GetValues()
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "EIRP (dBm)", "Path Loss (dB)", "Received Power (dBm)"])
            for i in range(len(times)):
                writer.writerow([times[i], eirp[i], path_loss[i], received_power[i]])
        print(f"[OK] Saved: {{file_path}}")

    def take_screenshot(self, file_path, view_mode="2D"):
        print(f"[INFO] Taking screenshot: {{file_path}}...")
        self.root.ExecuteCommand(f'VO * ViewMode {{view_mode}}')
        self.root.ExecuteCommand(f'VO * SaveImage \"{{file_path}}\"')
        print(f"[OK] Screenshot saved: {{file_path}}")

    def take_screenshot_at_time(self, file_path, time_str, view_mode="2D"):
        print(f"[INFO] Taking screenshot at {{time_str}}: {{file_path}}...")
        self.root.CurrentTime = time_str
        self.root.ExecuteCommand(f'VO * ViewMode {{view_mode}}')
        self.root.ExecuteCommand(f'VO * SaveImage \"{{file_path}}\"')
        print(f"[OK] Screenshot saved: {{file_path}}")

if __name__ == "__main__":
    print("\\n===== STK AUTOMATION STARTED =====\\n")
    try:
        stk = STKAutomation(visible=True)
        # IMPLEMENT THE USER'S SCENARIO HERE
        # Use all the methods above to create satellites, sensors, compute access, etc.
        # Generate ALL reports and screenshots requested
    except Exception as e:
        print(f"[ERROR] Automation failed: {{e}}")
        import traceback
        traceback.print_exc()
    print("\\n===== STK AUTOMATION COMPLETED =====\\n")

CRITICAL REQUIREMENTS:
1. ALWAYS use the STKAutomation class pattern shown above. Add more methods if needed.
2. Handle ALL aspects mentioned in the user's scenario:
   - Multiple satellites, aircraft, facilities, targets
   - Sensors and transmitters on objects
   - Access calculations between any objects
   - Link budgets for transmitter-receiver pairs
   - AER (Azimuth, Elevation, Range) reports
   - Coverage analysis
   - Screenshots at specific times or intervals
   - All CSV reports requested
3. Use proper error handling with try/except blocks.
4. Generate ALL reports and screenshots the user requests - don't skip anything.
5. Use relative paths for output files (e.g., "access_report.csv", "screenshot_0.png").
6. For screenshots at intervals (e.g., every 24 hours), loop through time and call take_screenshot_at_time().
7. If user mentions "India" or "Delhi", use approximate coordinates: Delhi ~ 28.6139°N, 77.2090°E.
8. For GEO satellites watching a region, use set_geo_orbit() with appropriate longitude.
9. Print [INFO] and [OK] messages for all major steps.

MOST IMPORTANT - OUTPUT FORMAT:
- Output ONLY raw Python code starting from the first import statement.
- DO NOT include markdown code blocks (no ```python, no ```, no backticks).
- DO NOT include any explanations, comments before code, or text after code.
- Start directly with: import csv
- End with the last line of your if __name__ == "__main__": block.
- Make the code COMPLETE and EXECUTABLE - implement EVERYTHING the user asks for.

User scenario description:
\"\"\"{user_text}\"\"\"
"""


def clean_gemini_code(raw_code: str) -> str:
    """
    Remove markdown code blocks if Gemini wrapped the code in them.
    Handles cases like: ```python ... ``` or ``` ... ```
    """
    code = raw_code.strip()
    
    # Remove markdown code blocks (```python ... ``` or ``` ... ```)
    if code.startswith("```"):
        # Find the first newline after ```
        first_newline = code.find("\n")
        if first_newline != -1:
            code = code[first_newline + 1:]
        else:
            code = code[3:]  # Remove just ```
    
    # Remove trailing ```
    if code.endswith("```"):
        code = code[:-3]
    
    return code.strip()


def call_gemini_and_get_code(prompt: str) -> str:
    """
    Call Gemini 2.5 Flash using google-genai and return the generated code.
    Automatically cleans markdown code blocks if present.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GOOGLE_GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
    )
    raw_code = getattr(response, "text", None)
    if not raw_code:
        raise RuntimeError("Gemini did not return any text/code.")
    
    # Clean markdown code blocks if present
    cleaned_code = clean_gemini_code(raw_code)
    return cleaned_code


def run_stk_script(code: str) -> Tuple[str, List[str]]:
    """
    Save the generated code to a temporary folder and run it with STK_PYTHON_CMD.

    Returns:
      - combined stdout+stderr (string)
      - list of artifact file paths (CSV / PNG) created by the script
    """
    work_dir = tempfile.mkdtemp(prefix="stk_job_")
    script_path = os.path.join(work_dir, "generated_stk.py")

    # Save the code to a file
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\n[INFO] Saved generated code to: {script_path}")
    print(f"[INFO] Working directory: {work_dir}")
    print(f"[TIP] You can review the generated code at: {script_path}")

    try:
        proc = subprocess.run(
            [STK_PYTHON_CMD, script_path],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=15 * 60,  # 15 minutes
        )
    except Exception as e:
        raise RuntimeError(f"Error running STK script: {e}")

    # Collect all artifacts (CSV, PNG, JPG, PDF, TXT, etc.)
    artifacts: List[str] = []
    for name in os.listdir(work_dir):
        lower = name.lower()
        if lower.endswith((".csv", ".png", ".jpg", ".jpeg", ".pdf", ".txt", ".xlsx", ".xls")):
            artifacts.append(os.path.join(work_dir, name))

    output_text = proc.stdout + "\n" + proc.stderr
    return output_text, artifacts


# ----------------------------
# CLI main
# ----------------------------

def main() -> None:
    """
    Simple terminal interface:
    - Ask for scenario description
    - Call Gemini
    - Run STK script
    - Show artifacts and truncated output
    """
    ensure_config_ok()

    print("="*60)
    print("  STK + Gemini Automation CLI")
    print("="*60)
    print("\nThis tool will:")
    print("  1. Ask Gemini 2.5 Flash to generate STK Python code")
    print("  2. Run the code using your STK Python interpreter")
    print("  3. Show you all generated reports and screenshots")
    print("\nSupported features:")
    print("  - Multiple satellites, aircraft, facilities, targets")
    print("  - Sensors, transmitters, receivers")
    print("  - Access calculations, link budgets, AER reports")
    print("  - Coverage analysis, screenshots at intervals")
    print("\n" + "-"*60)
    print("Describe your STK scenario in one or more lines.")
    print("When you are done, press Enter on an empty line.")
    print("-"*60 + "\n")

    # Read multi-line input from user
    lines = []
    while True:
        line = input("> ")
        if not line.strip():
            break
        lines.append(line)

    user_text = "\n".join(lines).strip()
    if not user_text:
        print("No scenario text provided. Exiting.")
        return

    print("\n[INFO] Calling Gemini to generate STK Python script...")
    prompt = build_gemini_prompt(user_text)

    try:
        generated_code = call_gemini_and_get_code(prompt)
    except Exception as e:
        logger.exception("Error while calling Gemini")
        print(f"[ERROR] Error while calling Gemini: {e}")
        return

    print("[INFO] Gemini returned code. Running STK script...")
    try:
        output_text, artifacts = run_stk_script(generated_code)
    except Exception as e:
        logger.exception("Error while running STK script")
        print(f"[ERROR] Error while running STK script: {e}")
        return

    if artifacts:
        print("\n" + "="*60)
        print(f"[SUCCESS] STK job finished. Generated {len(artifacts)} file(s):")
        print("="*60)
        for i, path in enumerate(artifacts, 1):
            file_size = os.path.getsize(path) / 1024  # Size in KB
            print(f"  {i}. {os.path.basename(path)} ({file_size:.2f} KB)")
            print(f"     Full path: {path}")
        print("="*60)
    else:
        print("\n[WARNING] STK job finished, but no output files (CSV/PNG/etc.) were found.")
        print("Check the script output below for errors.")

    print("\n" + "="*60)
    print("[INFO] Script execution output:")
    print("="*60)
    if output_text:
        # Show last 5000 chars (most recent output)
        display_text = output_text[-5000:] if len(output_text) > 5000 else output_text
        print(display_text)
    else:
        print("(No output captured)")
    print("="*60)


if __name__ == "__main__":
    main()
