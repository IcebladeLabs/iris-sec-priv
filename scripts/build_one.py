import os
import argparse
import csv
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.config import DATA_DIR, IRIS_ROOT_DIR, DEP_CONFIGS


ALLVERSIONS = json.load(open(DEP_CONFIGS))
ATTEMPTS = [
  { # Attempt 1
    "jdk": "8",
    "mvn": "3.5.0",
  },
  { # Attempt 2
    "jdk": "17",
    "mvn": "3.5.0",
  },
  { # Attempt 3
    "jdk": "17",
    "mvn": "3.9.8",
  },
  { # Attempt 4
    "jdk": "8",
    "mvn": "3.9.8",
  },
  { # Attempt 6
    "jdk": "17",
    "gradle": "8.9",
  },
  { # Attempt 7
    "jdk": "8",
    "gradle": "7.6.4",
  },
  { # Attempt 8
    "jdk": "8",
    "gradle": "6.8.2",
  },
  { # Attempt 9
    "jdk": "8",
    "gradlew": 1,
  },
  { # Attempt 10
    "jdk": "17",
    "gradlew": 1,
  }
]

NEWLY_BUILT = "newly-built"
ALREADY_BUILT = "already-built"
FAILED = "failed"

def build_one_project_with_maven_attempt(project_slug, attempt):
  target_dir = f"{DATA_DIR}/project-sources/{project_slug}"

  print(f">> [build_one] Building `{project_slug}` with MAVEN {attempt['mvn']} and JDK {attempt['jdk']}...")
  jdk_version = attempt.get('jdk')
  mvn_version = attempt.get('mvn', None)
  JAVA_PATH = ALLVERSIONS["jdks"].get(jdk_version, None)
  MAVEN_PATH = ALLVERSIONS["mvn"].get(mvn_version, None)
  if JAVA_PATH is None or MAVEN_PATH is None:
    print(f">> [build_one] JDK {jdk_version} or MAVEN {mvn_version} not found in available installations.")
    return FAILED
  if not os.path.exists(JAVA_PATH) or not os.path.exists(MAVEN_PATH):
    print(f">> [build_one] JDK {jdk_version} or MAVEN {mvn_version} not found in the filesystem.")
    return FAILED
  if not os.path.exists(f"{JAVA_PATH}/bin/java") or not os.path.exists(f"{MAVEN_PATH}/bin/mvn"):
    print(f">> [build_one] JDK {jdk_version} or MAVEN {mvn_version} not found in the filesystem (bin directory).")
    return FAILED

  print(f">> [build_one] JAVA_PATH: {JAVA_PATH}")
  print(f">> [build_one] MAVEN_PATH: {MAVEN_PATH}")
  print(f">> [build_one] Setting JDK version to {jdk_version} and MAVEN version to {mvn_version}") 
 
  # subprocess.run(["update-alternatives", "--set", "java", JAVA_PATH])
  # subprocess.run(["update-alternatives", "--set", "mvn", MAVEN_PATH])
  os.environ["JAVA_HOME"] = JAVA_PATH
  os.environ["MAVEN_HOME"] = MAVEN_PATH
  mvn_build_cmd = [
    "mvn",
    "clean",
    "package",
    "-B",
    "-V",
    "-e",
    "-Dfindbugs.skip",
    "-Dcheckstyle.skip",
    "-Dpmd.skip=true",
    "-Dspotbugs.skip",
    "-Denforcer.skip",
    "-Dmaven.javadoc.skip",
    "-DskipTests",
    "-Dmaven.test.skip.exec",
    "-Dlicense.skip=true",
    "-Drat.skip=true",
    "-Dspotless.check.skip=true"
  ]
  output = subprocess.run(
    mvn_build_cmd,
    cwd=target_dir,
    env={
      "PATH": f"{os.environ['PATH']}:{MAVEN_PATH}/bin",
      "JAVA_HOME": JAVA_PATH,
    },
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )

  if output.returncode != 0:
    print(f">> [build_one] Attempting build `{project_slug}` with MAVEN {attempt['mvn']} and JDK {attempt['jdk']} failed with return code {output.returncode}")
    print(f"StdOut:")
    print(output.stdout)
    print(f"Error message:")
    print(output.stderr)
    return FAILED
  else:
    print(f">> [build_one] Build succeeded for project `{project_slug}` with MAVEN {attempt['mvn']} and JDK {attempt['jdk']}")
    print(f">> [build_one] Dumping build information")
    json.dump(attempt, open(f"{DATA_DIR}/build-info/{project_slug}.json", "w"))
    return NEWLY_BUILT

def build_one_project_with_gradle_attempt(project_slug, attempt):
  target_dir = f"{DATA_DIR}/project-sources/{project_slug}"
  #JAVA_PATH = subprocess.run(["update-alternatives --list java | grep " + attempt['jdk'] + "| head -1" ] , shell=True, capture_output=True, text=True).stdout.strip()
  JAVA_PATH = ALLVERSIONS["jdks"].get(attempt['jdk'], None)
  GRADLE_PATH = ALLVERSIONS["gradle"].get(attempt['gradle'], None)
  if JAVA_PATH is None or GRADLE_PATH is None:
    print(f">> [build_one] JDK {attempt['jdk']} or Gradle {attempt['gradle']} not found in available installations.")
    return FAILED
  if not os.path.exists(JAVA_PATH) or not os.path.exists(GRADLE_PATH):
    print(f">> [build_one] JDK {attempt['jdk']} or Gradle {attempt['gradle']} not found in the filesystem.")
    return FAILED
  print(f">> [build_one] Building `{project_slug}` with Gradle {attempt['gradle']} and JDK {attempt['jdk']}...")
  gradle_build_cmd = [
    "gradle",
    "build",
    "--parallel",
  ]
  output = subprocess.run(
    gradle_build_cmd,
    cwd=target_dir,
    env={
      "PATH": f"{os.environ['PATH']}:{GRADLE_PATH}/bin",
      "JAVA_HOME": JAVA_PATH,
    },
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )

  if output.returncode != 0:
    print(f">> [build_one] Attempting build `{project_slug}` with Gradle {attempt['gradle']} and JDK {attempt['jdk']} failed with return code {output.returncode}")
    print(f"StdOut:")
    print(output.stdout)
    print(f"Error message:")
    print(output.stderr)
    return FAILED
  else:
    print(f">> [build_one] Build succeeded for project `{project_slug}` with Gradle {attempt['gradle']} and JDK {attempt['jdk']}")
    print(f">> [build_one] Dumping build information")
    json.dump(attempt, open(f"{DATA_DIR}/build-info/{project_slug}.json", "w"))
    return NEWLY_BUILT

def build_one_project_with_gradlew(project_slug, attempt):
  target_dir = f"{DATA_DIR}/project-sources/{project_slug}"
  print(f">> [build_one] Attempting build `{project_slug}` with custom gradlew script...")
  print(f">> [build_one] Chmod +x on gradlew file...")
  subprocess.run(["chmod", "+x", "./gradlew"], cwd=target_dir)
  print(f">> [build_one] Running gradlew...")
  output = subprocess.run(
    ["./gradlew", "--no-daemon", "-S", "-Dorg.gradle.dependency.verification=off", "clean"],
    cwd=target_dir,
    env={
      "JAVA_HOME": f"{ALLVERSIONS['jdks'][attempt['jdk']]}"
    },
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )
  if output.returncode != 0:
    print(f">> [build_one] Attempting build `{project_slug}` with ./gradlew and JDK {attempt['jdk']} failed with return code {output.returncode}")
    print(f"StdOut:")
    print(output.stdout)
    print(f"Error message:")
    print(output.stderr)
    return FAILED
  else:
    print(f">> [build_one] Build succeeded for project `{project_slug}` with ./gradlew and JDK {attempt['jdk']}")
    print(f">> [build_one] Dumping build information")
    json.dump({"gradlew": 1}, open(f"{DATA_DIR}/build-info/{project_slug}.json", "w"))
    return NEWLY_BUILT

def build_one_project_with_attempt(project_slug, attempt):
  # Checking if the repo has been built already
  if is_built(project_slug):
    print(f">> [build_one] {project_slug} is already built...")
    return ALREADY_BUILT

  # Otherwise, build it directly
  if "mvn" in attempt:
    return build_one_project_with_maven_attempt(project_slug, attempt)
  elif "gradle" in attempt:
    return build_one_project_with_gradle_attempt(project_slug, attempt)
  elif os.path.exists(f"{DATA_DIR}/project-sources/{project_slug}/gradlew"):
    return build_one_project_with_gradlew(project_slug, attempt)
  else:
    raise Exception("should not happen!")

def is_built(project_slug) -> bool:
  if os.path.exists(f"{DATA_DIR}/build-info/{project_slug}.json"):
    return True
  else:
    return False

def save_local_build_result(project_slug, result, attempt):
  build_result_dir = f"{DATA_DIR}/build-info/build_info_local.csv"

  # Create the build-info directory if it doesn't exist
  os.makedirs(os.path.dirname(build_result_dir), exist_ok=True)

  rows = []
  if os.path.exists(build_result_dir):
    rows = list(csv.reader(open(build_result_dir)))[1:]

  timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
  
  rows.append([
    timestamp,
    project_slug,
    "success" if result else "failure",
    attempt["jdk"],
    attempt["mvn"] if "mvn" in attempt else "n/a",
    attempt["gradle"] if "gradle" in attempt else "n/a",
    attempt["gradlew"] if "gradlew" in attempt else "n/a",
  ])

  writer = csv.writer(open(build_result_dir, "w"))
  writer.writerow(["timestamp", "project_slug", "status", "jdk_version", "mvn_version", "gradle_version", "use_gradlew"])
  writer.writerows(rows)

def get_build_info_from_csv(project_slug, csv_path):
  if not os.path.exists(csv_path):
    return None
    
  print(f">> [build_one] Checking build info from {csv_path}")
  try:
    with open(csv_path) as f:
      reader = csv.DictReader(f)
      for row in reader:
        if row['project_slug'] == project_slug and row['status'] == 'success':
          specific_attempt = {}
          if row['jdk_version'] != 'n/a':
            specific_attempt['jdk'] = row['jdk_version']
          if row['mvn_version'] != 'n/a':
            specific_attempt['mvn'] = row['mvn_version']
          if row['gradle_version'] != 'n/a':
            specific_attempt['gradle'] = row['gradle_version']
          if row['use_gradlew'] != 'n/a':
            specific_attempt['gradlew'] = int(row['use_gradlew'])

          # Check if we have a JDK and a build tool configuration
          if 'jdk' in specific_attempt and any(key in specific_attempt for key in ['mvn', 'gradle', 'gradlew']):
            print(f">> [build_one] Found successful build configuration: {specific_attempt}")
            return specific_attempt
  except Exception as e:
    print(f">> [build_one] Failed to read or use build info from CSV: {str(e)}")
  
  return None

def try_build_with_attempt(project_slug, attempt, attempt_source=""):
  """Try to build a project with a specific attempt configuration."""
  if attempt_source:
    print(f">> [build_one] Using {attempt_source} build configuration: {attempt}")
  
  result = build_one_project_with_attempt(project_slug, attempt)
  if result == NEWLY_BUILT:
    save_local_build_result(project_slug, True, attempt)
    return True
  elif result == ALREADY_BUILT:
    return True
  else:
    save_local_build_result(project_slug, False, attempt)
    return False

def build_one_project(project_slug, try_all=False, custom_attempt=None):
  # Handle custom attempt first
  if custom_attempt:
    if try_build_with_attempt(project_slug, custom_attempt, "custom"):
      return
    print(f">> [build_one] Custom build configuration failed for {project_slug}")
    return

  # Try known configurations unless try_all is True
  if not try_all:
    # Try local build info first
    local_build_info = get_build_info_from_csv(project_slug, f"{DATA_DIR}/build-info/build_info_local.csv")
    if local_build_info and try_build_with_attempt(project_slug, local_build_info, "local"):
      return
    
    # Try global build info if local failed
    global_build_info = get_build_info_from_csv(project_slug, f"{DATA_DIR}/build_info.csv")
    if global_build_info and try_build_with_attempt(project_slug, global_build_info, "global"):
      return

  # Try all default attempts
  print(">> [build_one] " + 
        ("Skipping build info check and trying all version combinations..." if try_all else 
         "No successful build configuration found in CSV files, trying all version combinations..."))

  for attempt in ATTEMPTS:
    if try_build_with_attempt(project_slug, attempt):
      return

def validate_and_create_custom_attempt(jdk, mvn, gradle, gradlew):
  """Validate the provided versions against dep_configs.json and create a custom attempt."""
  if not jdk:
    print(">> [build_one] Error: JDK version must be specified when using custom versions")
    sys.exit(1)
  
  # Validate JDK version
  if jdk not in ALLVERSIONS["jdks"]:
    available_jdks = list(ALLVERSIONS["jdks"].keys())
    print(f">> [build_one] Error: JDK version '{jdk}' not found. Available JDK versions: {available_jdks}")
    sys.exit(1)
  
  custom_attempt = {"jdk": jdk}
  build_tool_count = 0
  
  # Validate and add Maven if specified
  if mvn:
    if mvn not in ALLVERSIONS["mvn"]:
      available_mvn = list(ALLVERSIONS["mvn"].keys())
      print(f">> [build_one] Error: Maven version '{mvn}' not found. Available Maven versions: {available_mvn}")
      sys.exit(1)
    custom_attempt["mvn"] = mvn
    build_tool_count += 1
  
  # Validate and add Gradle if specified
  if gradle:
    if gradle not in ALLVERSIONS["gradle"]:
      available_gradle = list(ALLVERSIONS["gradle"].keys())
      print(f">> [build_one] Error: Gradle version '{gradle}' not found. Available Gradle versions: {available_gradle}")
      sys.exit(1)
    custom_attempt["gradle"] = gradle
    build_tool_count += 1
  
  # Add gradlew if specified
  if gradlew:
    custom_attempt["gradlew"] = 1
    build_tool_count += 1
  
  # Ensure exactly one build tool is specified
  if build_tool_count == 0:
    print(">> [build_one] Error: At least one build tool must be specified (--mvn, --gradle, or --gradlew)")
    sys.exit(1)
  elif build_tool_count > 1:
    print(">> [build_one] Error: Only one build tool can be specified at a time (--mvn, --gradle, or --gradlew)")
    sys.exit(1)
  
  return custom_attempt

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("project_slug", type=str)
  parser.add_argument("--try_all", action="store_true", help="Skip build info check and try all version combinations")
  
  # Custom version arguments
  parser.add_argument("--jdk", type=str, help="Specific JDK version to use (e.g., '8', '11', '17')")
  parser.add_argument("--mvn", type=str, help="Specific Maven version to use (e.g., '3.5.0', '3.9.8')")
  parser.add_argument("--gradle", type=str, help="Specific Gradle version to use (e.g., '6.8.2', '7.6.4', '8.9')")
  parser.add_argument("--gradlew", action="store_true", help="Use the project's gradlew script")
  
  args = parser.parse_args()
  
  # Check if custom versions are specified
  custom_attempt = None
  if args.jdk or args.mvn or args.gradle or args.gradlew:
    if args.try_all:
      print(">> [build_one] Error: Cannot use --try_all with custom version arguments")
      sys.exit(1)
    custom_attempt = validate_and_create_custom_attempt(args.jdk, args.mvn, args.gradle, args.gradlew)
  
  build_one_project(args.project_slug, try_all=args.try_all, custom_attempt=custom_attempt)
