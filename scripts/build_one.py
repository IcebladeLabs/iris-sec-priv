import os
import argparse
import csv
import subprocess
import json
import sys
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
ALREDY_BUILT = "already-built"
FAILED = "failed"

def build_one_project_with_maven_attempt(project_slug, attempt):
  target_dir = f"{DATA_DIR}/project-sources/{project_slug}"

  print(f">> [build_one] Building `{project_slug}` with MAVEN {attempt['mvn']} and JDK {attempt['jdk']}...")
  jdk_version = attempt.get('jdk']
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
    return ALREDY_BUILT

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

def save_build_result(project_slug, result, attempt):
  build_result_dir = f"{DATA_DIR}/build_info.csv"

  rows = []
  if os.path.exists(build_result_dir):
    rows = list(csv.reader(open(build_result_dir)))[1:]

  existed_and_mutated = False
  desired_num_columns = 6
  for row in rows:
    if len(row) < desired_num_columns:
      row += ["n/a"] * (desired_num_columns - len(row))
    if row[0] == project_slug:
      existed_and_mutated = True
      row[1] = "success" if result else "failure"
      row[2] = attempt["jdk"]
      row[3] = attempt["mvn"] if "mvn" in attempt else "n/a"
      row[4] = attempt["gradle"] if "gradle" in attempt else "n/a"
      row[5] = attempt["gradlew"] if "gradlew" in attempt else "n/a"

  if not existed_and_mutated:
    rows.append([
      project_slug,
      "success" if result else "failure",
      attempt["jdk"],
      attempt["mvn"] if "mvn" in attempt else "n/a",
      attempt["gradle"] if "gradle" in attempt else "n/a",
      attempt["gradlew"] if "gradlew" in attempt else "n/a",
    ])

  writer = csv.writer(open(build_result_dir, "w"))
  writer.writerow(["project_slug", "status", "jdk_version", "mvn_version", "gradle_version", "use_gradlew"])
  writer.writerows(rows)

def build_one_project(project_slug):
  for attempt in ATTEMPTS:
      result = build_one_project_with_attempt(project_slug, attempt)
      if result == NEWLY_BUILT:
        save_build_result(project_slug, True, attempt)
        return
      elif result == ALREDY_BUILT:
        return
      save_build_result(project_slug, False, {"jdk": "n/a", "mvn": "n/a", "gradle": "n/a"})

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("project_slug", type=str)
  args = parser.parse_args()
  build_one_project(args.project_slug)
