#!/bin/bash
# =============================================================================
#  setup_mt5_wine.sh
#  Install Wine + MT5 di Linux (Ubuntu/Debian)
#  Jalankan sebagai user biasa (bukan root)
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }

echo ""
echo "======================================================="
echo "  MT5 + Wine Setup untuk Linux"
echo "  Project: OpenClaw Trading Reporter"
echo "======================================================="
echo ""

# ── Cek distro ───────────────────────────────────────────────────────────────
if ! command -v apt-get &>/dev/null; then
    err "Script ini untuk Ubuntu/Debian. Untuk distro lain, install Wine secara manual."
    exit 1
fi

# ── Tambah arsitektur 32-bit (Wine butuh ini) ────────────────────────────────
info "Menambahkan arsitektur i386..."
sudo dpkg --add-architecture i386

# ── Install Wine ─────────────────────────────────────────────────────────────
info "Menginstall Wine..."
sudo apt-get update -q
sudo apt-get install -y wine wine32 wine64 winetricks xvfb

log "Wine terinstall: $(wine --version)"

# ── Buat WINEPREFIX khusus MT5 ───────────────────────────────────────────────
export WINEPREFIX="$HOME/.wine_mt5"
export WINEARCH=win64

info "Inisialisasi Wine prefix untuk MT5 di: $WINEPREFIX"
wineboot --init 2>/dev/null || true

# Install dotnet dan Visual C++ runtime (MT5 butuh ini)
info "Menginstall dependencies MT5 via winetricks..."
winetricks -q vcrun2019 || warn "vcrun2019 gagal, lanjutkan..."
winetricks -q corefonts || warn "corefonts gagal, lanjutkan..."

# ── Download MT5 installer ───────────────────────────────────────────────────
MT5_INSTALLER="$HOME/mt5setup.exe"

if [ ! -f "$MT5_INSTALLER" ]; then
    info "Download MT5 installer..."
    wget -q --show-progress \
        "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" \
        -O "$MT5_INSTALLER"
    log "MT5 installer downloaded."
else
    info "MT5 installer sudah ada: $MT5_INSTALLER"
fi

# ── Install MT5 ──────────────────────────────────────────────────────────────
info "Menjalankan MT5 installer via Wine..."
info "(Ikuti wizard instalasi di jendela yang muncul)"

DISPLAY=${DISPLAY:-:0} WINEPREFIX="$HOME/.wine_mt5" wine "$MT5_INSTALLER" &
INSTALL_PID=$!
wait $INSTALL_PID || true

# ── Buat folder data sync ─────────────────────────────────────────────────────
MT5_DATA="$HOME/mt5_data"
mkdir -p "$MT5_DATA"

# Symlink ke folder Files MT5 (tempat EA export CSV)
MT5_FILES="$HOME/.wine_mt5/drive_c/Program Files/MetaTrader 5/MQL5/Files"
if [ -d "$MT5_FILES" ]; then
    ln -sf "$MT5_FILES" "$MT5_DATA/mt5_files"
    log "Symlink dibuat: $MT5_DATA/mt5_files -> $MT5_FILES"
else
    warn "Folder MT5 Files belum ditemukan. Install MT5 dulu, lalu jalankan:"
    warn "  ln -s \"$MT5_FILES\" \"$MT5_DATA/mt5_files\""
fi

# ── Buat script launcher MT5 ─────────────────────────────────────────────────
LAUNCHER="$HOME/bin/mt5"
mkdir -p "$HOME/bin"

cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
# Launcher MT5 via Wine
export WINEPREFIX="$HOME/.wine_mt5"
export WINEARCH=win64

MT5_EXE=$(find "$WINEPREFIX/drive_c" -name "terminal64.exe" 2>/dev/null | head -1)

if [ -z "$MT5_EXE" ]; then
    echo "MT5 belum terinstall atau tidak ditemukan."
    echo "Cari manual: find ~/.wine_mt5 -name '*.exe' | grep -i terminal"
    exit 1
fi

echo "Launching MT5: $MT5_EXE"
DISPLAY=${DISPLAY:-:0} wine "$MT5_EXE" "$@" &
echo "MT5 berjalan (PID: $!)"
LAUNCHER_EOF

chmod +x "$LAUNCHER"
log "Launcher dibuat: $LAUNCHER"
info "Jalankan MT5 kapanpun dengan: mt5"

# ── Setup Python dependencies ─────────────────────────────────────────────────
info "Menginstall Python dependencies..."
pip3 install requests pandas --quiet --break-system-packages 2>/dev/null || \
pip3 install requests pandas --quiet 2>/dev/null || \
warn "pip install gagal, coba manual: pip3 install requests pandas"

log "Python dependencies OK"

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "======================================================="
echo -e "${GREEN}  Setup selesai!${NC}"
echo "======================================================="
echo ""
echo "Langkah selanjutnya:"
echo ""
echo "  1. Buka MT5:"
echo "     mt5"
echo ""
echo "  2. Di MT5, copy TradeExporter.mq5 ke:"
echo "     $HOME/.wine_mt5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/"
echo "     Lalu compile dan attach ke chart"
echo ""
echo "  3. Setup config Python:"
echo "     python3 ~/mt5_openclaw/python/trade_summary.py --setup"
echo "     nano ~/.openclaw/trade_config.json"
echo ""
echo "  4. Test kirim summary:"
echo "     python3 ~/mt5_openclaw/python/trade_summary.py --period today --dry-run"
echo ""
echo "  5. Setup OpenClaw skill:"
echo "     Salin file dari ~/mt5_openclaw/openclaw_skill/"
echo ""
