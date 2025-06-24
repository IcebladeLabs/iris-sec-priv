# FOLIO spring-module-core CVE-2022-4963 PoC runner                                         
#                                                                             
# This script uses the pre-built JARs from the project-sources directory and  
# ensures all required dependencies are available.                  

echo "=== CVE-2022-4963 FOLIO spring-module-core SQL Injection PoC ==="
echo "This PoC tests the vulnerable CQL2WhereClauseParser methods"
echo

# Paths for source and build artifacts
FOLIO_SOURCE_DIR="/iris/data/project-sources/folio-org__spring-module-core_CVE-2022-4963_2.0.0"
DOMAIN_JAR="$FOLIO_SOURCE_DIR/domain/target/spring-domain-1.1.3-SNAPSHOT.jar"
TENANT_JAR="$FOLIO_SOURCE_DIR/tenant/target/spring-tenant-1.1.3-SNAPSHOT.jar"
WEB_JAR="$FOLIO_SOURCE_DIR/web/target/spring-web-1.1.3-SNAPSHOT.jar"
BUILD_DIR="target/classes"
DEPS_DIR="deps"
SETUP_SCRIPT="/iris/scripts/setup.py"

# Constants for the two commits of interest
VULNERABLE_COMMIT="e93b5ddd3022b81abf8ae81da8d3a740186f456e"
FIXED_COMMIT="d374a5f77e6b58e36f0e0e4419be18b95edcd7ff"

# Function to check and build repository if needed
check_and_build_repo() {
    echo "[INFO] Checking for required JARs..."
    
    if [ ! -f "$DOMAIN_JAR" ] || [ ! -f "$TENANT_JAR" ] || [ ! -f "$WEB_JAR" ]; then
        echo "[INFO] One or more required JARs not found. Building repository..."
        if [ ! -f "$SETUP_SCRIPT" ]; then
            echo "[ERROR] Setup script not found at: $SETUP_SCRIPT"
            echo "        Please ensure you are running this from the IRIS project root"
            exit 1
        fi
        
        echo "[INFO] Running setup script to fetch and build repository..."
        if ! python3 "$SETUP_SCRIPT" --filter folio-org__spring-module-core_CVE-2022-4963_2.0.0; then
            echo "[ERROR] Failed to build repository"
            exit 1
        fi
        
        # Double check if JARs were built
        if [ ! -f "$DOMAIN_JAR" ] || [ ! -f "$TENANT_JAR" ] || [ ! -f "$WEB_JAR" ]; then
            echo "[ERROR] Repository build completed but one or more JARs still not found"
            echo "        Expected locations:"
            echo "        - $DOMAIN_JAR"
            echo "        - $TENANT_JAR"
            echo "        - $WEB_JAR"
            exit 1
        fi
        
        echo "[INFO] Repository built successfully"
    fi
}

# Function to check if required tools exist
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
    
    # Check if SLF4J is already downloaded (for logging)
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
    echo "[INFO] Compiling the PoC …"
    rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR"
    CLASSPATH="$DOMAIN_JAR:$TENANT_JAR:$WEB_JAR:$DEPS_DIR/*"
    if ! javac -encoding UTF-8 -cp "$CLASSPATH" -d "$BUILD_DIR" FolioSpringModuleCoreSQLiPoCTest.java; then
        echo "[ERROR] Compilation failed" >&2
        exit 1
    fi
    echo "[INFO] Compilation successful"
}

# Utility: (re-)build all three sub-modules via Maven
build_with_maven() {
    local src_dir="$1"
    echo "[INFO] Running Maven build inside $src_dir …"
    if ! mvn -q -pl domain,tenant,web -am -DskipTests -f "$src_dir/pom.xml" clean package; then
        echo "[ERROR] Maven build failed in $src_dir" >&2
        exit 1
    fi
}

# Switch the working copy from the vulnerable to the fixed commit
checkout_fixed_commit() {
    echo
    echo "[INFO] Switching repository to FIXED commit $FIXED_COMMIT …"

    # Ensure we have sufficient history (shallow clone created by fetch_one has depth 1)
    git -C "$FOLIO_SOURCE_DIR" fetch --unshallow -q 2>/dev/null || true
    # Fetch the actual commit (may still be outside current shallow history)
    git -C "$FOLIO_SOURCE_DIR" fetch -q origin "$FIXED_COMMIT" --depth 1 || {
        echo "[ERROR] Unable to fetch commit $FIXED_COMMIT from remote." >&2
        exit 1
    }

    # Finally checkout
    git -C "$FOLIO_SOURCE_DIR" checkout -q "$FIXED_COMMIT" || {
        echo "[ERROR] git checkout failed for $FIXED_COMMIT" >&2
        exit 1
    }

    echo "[INFO] Checked out fixed commit successfully. Re-building …"
    build_with_maven "$FOLIO_SOURCE_DIR"
}

# Function to run the PoC
run_poc() {
    local label="$1"   # e.g. "VULNERABLE" / "FIXED"
    echo "[INFO] Running vulnerability demonstration ($label build) …"
    echo "-----------------------------------------------"
    # Build runtime classpath
    RUNTIME_CLASSPATH="$BUILD_DIR:$DOMAIN_JAR:$TENANT_JAR:$WEB_JAR:$DEPS_DIR/*"
    # Run
    java -cp "$RUNTIME_CLASSPATH" FolioSpringModuleCoreSQLiPoCTest || true
}

# Function to clean up
cleanup() {
    echo "[INFO] Cleaning up build artifacts..."
    rm -rf "$BUILD_DIR"
    echo "[INFO] Cleanup completed"
}

# Main execution logic
check_prerequisites
check_and_build_repo          # builds vulnerable commit jars
setup_dependencies
compile_poc
run_poc "VULNERABLE"

# --- test fixed commit -----------------------------------------------------------------
checkout_fixed_commit         # switches repo & rebuilds jars
compile_poc                   # re-compile against freshly built jars
run_poc "FIXED"

# -------------------------------------------------------------------------
# Switch back to vulnerable commit so repository remains in original state
# -------------------------------------------------------------------------

echo
echo "[INFO] Restoring repository to vulnerable commit $VULNERABLE_COMMIT …"

git -C "$FOLIO_SOURCE_DIR" checkout -q "$VULNERABLE_COMMIT" || {
    echo "[ERROR] git checkout failed for $VULNERABLE_COMMIT (restore phase)" >&2
    # do not exit – keeping fixed commit is acceptable, but warn
}

build_with_maven "$FOLIO_SOURCE_DIR"
compile_poc  # rebuild PoC against restored jars

cleanup

echo "[INFO] PoC execution completed"
