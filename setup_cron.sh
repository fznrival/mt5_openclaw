#!/bin/bash
# =============================================================================
#  setup_cron.sh
#  Daftarkan cron job untuk auto-kirim trading report
# =============================================================================

PYTHON="python3"
SCRIPT="$HOME/mt5_openclaw/python/trade_summary.py"
LOGFILE="/tmp/trade_summary_cron.log"

echo "Setting up cron jobs untuk MT5 Trading Reporter..."

# Backup crontab lama
crontab -l 2>/dev/null > /tmp/crontab_backup.txt
echo "Backup crontab lama: /tmp/crontab_backup.txt"

# Buat crontab baru (tambah ke existing)
(
  crontab -l 2>/dev/null | grep -v "trade_summary"  # Hapus entry lama jika ada

  # Daily report — Senin s/d Jumat jam 23:00 WIB (16:00 UTC)
  echo "0 16 * * 1-5 $PYTHON $SCRIPT --period today >> $LOGFILE 2>&1"

  # Weekly report — Jumat jam 23:30 WIB (16:30 UTC)
  echo "30 16 * * 5 $PYTHON $SCRIPT --period week >> $LOGFILE 2>&1"

  # Monthly report — Hari terakhir bulan jam 23:45 WIB (16:45 UTC)
  echo "45 16 28-31 * * [ \"\$(date +\\%d -d tomorrow)\" = '01' ] && $PYTHON $SCRIPT --period month >> $LOGFILE 2>&1"

) | crontab -

echo ""
echo "Cron jobs terdaftar:"
crontab -l | grep trade_summary
echo ""
echo "Log cron tersimpan di: $LOGFILE"
echo ""
echo "Untuk lihat log:"
echo "  tail -f $LOGFILE"
echo ""
echo "Untuk hapus cron jobs:"
echo "  crontab -l | grep -v trade_summary | crontab -"
