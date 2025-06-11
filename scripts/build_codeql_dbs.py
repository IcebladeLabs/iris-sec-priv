import csv
import os
import argparse
import subprocess
from pathlib import Path
import sys
import json
sys.path.append(str(Path(__file__).parent.parent))

from src.config import CODEQL_DB_PATH, PROJECT_SOURCE_CODE_DIR, IRIS_ROOT_DIR, BUILD_INFO, DEP_CONFIGS, DATA_DIR
ALLVERSIONS = json.load(open(DEP_CONFIGS))

def setup_environment(row):
    env = os.environ.copy()
    
    # Set Maven path if available
    if row['mvn_version'] != 'n/a':
        MAVEN_PATH = ALLVERSIONS['mvn'].get(row['mvn_version'], None)
        env['PATH'] = f"{MAVEN_PATH}:{env.get('PATH', '')}"
        print(f"Maven path set to: {MAVEN_PATH}")

    # Find and set Java home
    java_version = row['jdk_version']
    java_home = ALLVERSIONS['jdks'].get(row['jdk_version'], None)
    if not java_home:
        raise Exception(f"Java version {java_version} not found in available installations.")

    env['JAVA_HOME'] = java_home
    print(f"JAVA_HOME set to: {java_home}")
    
    # Add Java binary to PATH
    env['PATH'] = f"{os.path.join(java_home, 'bin')}:{env.get('PATH', '')}"
    
    return env

def create_codeql_database(project_slug, env, db_base_path, sources_base_path):
    print("\nEnvironment variables for CodeQL database creation:")
    print(f"PATH: {env.get('PATH', 'Not set')}")
    print(f"JAVA_HOME: {env.get('JAVA_HOME', 'Not set')}")
    
    try:
        java_version = subprocess.check_output(['java', '-version'], 
                                            stderr=subprocess.STDOUT, 
                                            env=env).decode()
        print(f"\nJava version check:\n{java_version}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking Java version: {e}")
        raise
    
    database_path = os.path.abspath(os.path.join(db_base_path, project_slug))
    source_path = os.path.abspath(os.path.join(sources_base_path, project_slug))
    
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    
    command = [
        "codeql", "database", "create",
        database_path,
        "--source-root", source_path,
        "--language", "java",
        "--overwrite"
    ]
    
    try:
        print(f"Creating database at: {database_path}")
        print(f"Using source path: {source_path}")
        print(f"Using JAVA_HOME: {env.get('JAVA_HOME', 'Not set')}")
        res=subprocess.run(command, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            print(f"Error creating CodeQL database: {res.stderr.decode()} \n {res.stdout.decode()}")
            raise subprocess.CalledProcessError(res.returncode, command, output=res.stdout, stderr=res.stderr)
        print(f"Successfully created CodeQL database for {project_slug}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating CodeQL database for {project_slug}: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Create CodeQL databases for cwe-bench-java projects')
    parser.add_argument('--project', help='Specific project slug', default=None)
    parser.add_argument('--db-path', help='Base path for storing CodeQL databases', default=CODEQL_DB_PATH)
    parser.add_argument('--sources-path', help='Base path for project sources', default=PROJECT_SOURCE_CODE_DIR)
    args = parser.parse_args()

    with open(BUILD_INFO, 'r') as f:
        reader = csv.DictReader(f)
        projects = list(reader)
    
    if args.project:
        project = next((p for p in projects if p['project_slug'] == args.project), None)
        if project:
            env = setup_environment(project)
            create_codeql_database(project['project_slug'], env, args.db_path, args.sources_path)
        else:
            print(f"Project {args.project} not found in CSV file")
    else:
        for project in projects:
            env = setup_environment(project)
            create_codeql_database(project['project_slug'], env, args.db_path, args.sources_path)

if __name__ == "__main__":
    main()