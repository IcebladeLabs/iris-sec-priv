# JeecgBoot CVE-2022-45206 PoC runner                                         
#                                                                             
# This script uses the pre-built JAR from the project-sources directory and  
# downloads only the minimal required dependencies (SLF4J).                  

echo "=== CVE-2022-45206 JeecgBoot SQL Injection PoC ==="
echo "This PoC directly tests the vulnerable SqlInjectionUtil methods"
echo

# Paths for 
JEECG_SOURCE_DIR="/iris/data/project-sources/jeecgboot__jeecgboot_CVE-2022-45206_3.4.3"
JEECG_JAR=""  # will be resolved dynamically
BUILD_DIR="target/classes"
DEPS_DIR="deps"
SETUP_SCRIPT="/iris/scripts/setup.py"

VULNERABLE_COMMIT="d34614c4224ec1af69d0d81329d84fe98e11f694"
FIXED_COMMIT="f18ced524c9ec13e876bfb74785a1b112cc8b6bb"

# Function to check and build repository if needed
check_and_build_repo() {
    update_jar_path
    if [ ! -f "$JEECG_JAR" ]; then
        echo "[INFO] JeecgBoot JAR not found. Building repository…"
        if [ ! -f "$SETUP_SCRIPT" ]; then
            echo "[ERROR] Setup script not found at: $SETUP_SCRIPT"
            echo "        Please ensure you are running this from the IRIS project root"
            exit 1
        fi
        
        echo "[INFO] Running setup script to fetch and build repository…"
        if ! python3 "$SETUP_SCRIPT" --filter jeecgboot__jeecgboot_CVE-2022-45206_3.4.3; then
            echo "[ERROR] Failed to build repository"
            exit 1
        fi
        
        # Double check if JAR was built
        update_jar_path
        if [ ! -f "$JEECG_JAR" ]; then
            echo "[ERROR] Repository build completed but JAR still not found"
            echo "        Expected location: $JEECG_JAR"
            exit 1
        fi
        
        echo "[INFO] Repository built successfully"
    fi
}

# Function to check if required files exist
check_prerequisites() {
    echo "[INFO] Checking prerequisites..."
    
    if ! command -v java &> /dev/null; then
        echo "[ERROR] Java is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v javac &> /dev/null; then
        echo "[ERROR] Java compiler (javac) is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v mvn &> /dev/null; then
        echo "[ERROR] Maven is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "[ERROR] Python3 is not installed or not in PATH"
        exit 1
    fi
    
    echo "[INFO] Prerequisites check passed"
}

# Function to setup minimal dependencies
setup_dependencies() {
    echo "[INFO] Setting up minimal dependencies..."
    
    # Create deps directory if it doesn't exist
    mkdir -p "$DEPS_DIR"
    
    # Check if SLF4J is already downloaded
    if [ ! -f "$DEPS_DIR/slf4j-api-1.7.36.jar" ]; then
        echo "[INFO] Downloading SLF4J API..."
        if ! mvn dependency:copy -Dartifact=org.slf4j:slf4j-api:1.7.36 -DoutputDirectory="$DEPS_DIR" -q; then
            echo "[ERROR] Failed to download SLF4J API"
            exit 1
        fi
    fi
    
    # Check if SLF4J Simple is already downloaded (for logging implementation)
    if [ ! -f "$DEPS_DIR/slf4j-simple-1.7.36.jar" ]; then
        echo "[INFO] Downloading SLF4J Simple..."
        if ! mvn dependency:copy -Dartifact=org.slf4j:slf4j-simple:1.7.36 -DoutputDirectory="$DEPS_DIR" -q; then
            echo "[ERROR] Failed to download SLF4J Simple"
            exit 1
        fi
    fi
    
    echo "[INFO] Dependencies setup completed"
}

# Function to compile the PoC
compile_poc() {
    echo "[INFO] Compiling PoC sources …"
    rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR"
    CLASSPATH="$JEECG_JAR:$DEPS_DIR/*"
    javac -encoding UTF-8 -cp "$CLASSPATH" -d "$BUILD_DIR" JeecgBootSQLiPoCTest.java || {
        echo "[ERROR] Compilation failed" >&2
        exit 1
    }
}

# Function to run the PoC
run_poc() {
    local label="$1"
    echo "[INFO] Running PoC ($label build) …"
    echo "-----------------------------------------------"
    RUNTIME_CLASSPATH="$BUILD_DIR:$JEECG_JAR:$DEPS_DIR/*"
    java -cp "$RUNTIME_CLASSPATH" JeecgBootSQLiPoCTest || true
}

# Function to clean up
cleanup() {
    echo "[INFO] Cleaning up build artifacts..."
    rm -rf "$BUILD_DIR"
    echo "[INFO] Cleanup completed"
}

update_jar_path() {
    local found
    found=$(ls "$JEECG_SOURCE_DIR/jeecg-boot-base-core/target" 2>/dev/null | grep -E "^jeecg-boot-base-core-.*\\.jar$" | head -1)
    JEECG_JAR="$JEECG_SOURCE_DIR/jeecg-boot-base-core/target/$found"
}

build_with_maven() {
    local src_dir="$1"
    echo "[INFO] Running Maven build in $src_dir …"
    mvn -q -pl jeecg-boot-base-core -am -DskipTests -f "$src_dir/pom.xml" clean package || {
        echo "[ERROR] Maven build failed" >&2
        exit 1
    }
}

checkout_and_rebuild() {
    local commit_hash="$1"; local label="$2"
    checkout_commit "$commit_hash"
    build_with_maven "$JEECG_SOURCE_DIR"
    update_jar_path
    compile_poc
    run_poc "$label"
}

checkout_commit() {
    git -C "$JEECG_SOURCE_DIR" fetch --unshallow -q 2>/dev/null || true
    git -C "$JEECG_SOURCE_DIR" fetch -q origin "$1" --depth 1 || true
    git -C "$JEECG_SOURCE_DIR" checkout -q "$1" || {
        echo "[ERROR] Could not checkout $1" >&2
        exit 1
    }
}

# Main execution
check_prerequisites
check_and_build_repo   # ensures vulnerable commit jars exist; does not change commit
update_jar_path
setup_dependencies
compile_poc
run_poc "VULNERABLE"

# Test fixed commit
checkout_and_rebuild "$FIXED_COMMIT" "FIXED"

echo
echo "[INFO] Restoring repository to vulnerable commit $VULNERABLE_COMMIT …"
checkout_commit "$VULNERABLE_COMMIT"
# Rebuild jars to leave workspace in a consistent state (no PoC execution)
build_with_maven "$JEECG_SOURCE_DIR"
update_jar_path

cleanup

echo "[INFO] PoC execution completed"
