#!/bin/bash
set -e

# --- Configuration ---
APP_NAME="PixelPuritan"
INSTALL_DIR="$HOME/.local/share/PixelPuritan"
BIN_DIR="$HOME/.local/bin"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️  Installing ${APP_NAME}...${NC}"

# 1. Prepare Directories
echo -e "${BLUE}📂 Setting up directories in $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy source files to install dir (excludes .git if present)
cp -r "$CURRENT_DIR/bin" "$INSTALL_DIR/"
cp -r "$CURRENT_DIR/src" "$INSTALL_DIR/"
cp -r "$CURRENT_DIR/server" "$INSTALL_DIR/"

# 2. Compile Rust Splitter
echo -e "${BLUE}⚙️  Compiling Rust Splitter module...${NC}"
if command -v rustc &> /dev/null; then
    rustc -O "$INSTALL_DIR/src/splitter/main.rs" -o "$INSTALL_DIR/src/splitter/pp-split"
    echo -e "${GREEN}✅ Compilation successful.${NC}"
else
    echo -e "${RED}❌ Error: 'rustc' not found. Install with: sudo pacman -S rust${NC}"
    exit 1
fi

# 3. Setup Python Client Wrapper (pp-scan)
echo -e "${BLUE}🐍 Configuring Python Client (pp-scan)...${NC}"
chmod +x "$INSTALL_DIR/src/client/nsfw_tool.py"

# Create a shim for the python tool
cat <<EOF > "$INSTALL_DIR/bin/pp-scan"
#!/bin/bash
# Wrapper for PixelPuritan Client
# Ensure dependencies are installed: pip install typer aiohttp rich
python3 "$INSTALL_DIR/src/client/nsfw_tool.py" "\$@"
EOF
chmod +x "$INSTALL_DIR/bin/pp-scan"
ln -sf "$INSTALL_DIR/bin/pp-scan" "$BIN_DIR/pp-scan"

# 4. Link Orchestrator (pp-batcher)
echo -e "${BLUE}🔗 Linking Orchestrator (pp-batcher)...${NC}"
chmod +x "$INSTALL_DIR/bin/pp-batcher"
ln -sf "$INSTALL_DIR/bin/pp-batcher" "$BIN_DIR/pp-batcher"

# 5. Docker Server Setup
echo -e "${BLUE}🐳 checking Docker environment...${NC}"
if command -v docker &> /dev/null; then
    echo -e "   Do you want to build/start the AI Server now? (y/n)"
    read -r -n 1 response
    echo
    if [[ "$response" =~ ^[yY]$ ]]; then
        echo -e "${BLUE}   Building container (this will take time)...${NC}"
        cd "$INSTALL_DIR/server"

        # Kill anything blocking port 8000
        sudo fuser -k 8000/tcp 2>/dev/null || true

        docker compose up -d --build
        echo -e "${GREEN}✅ Server started. Model will download in background.${NC}"
        echo -e "   View logs with: docker logs -f pixelpuritan-ai"
    fi
else
    echo -e "${RED}⚠️  Docker not found. Skipping server setup.${NC}"
fi

echo -e "------------------------------------------------"
echo -e "${GREEN}🎉 PixelPuritan Installed Successfully!${NC}"
echo -e "   • Split & Scan:  ${GREEN}pp-batcher <folder>${NC}"
echo -e "   • Manual Scan:   ${GREEN}pp-scan <folder>${NC}"
