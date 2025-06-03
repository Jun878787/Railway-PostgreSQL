#!/usr/bin/env python3
import asyncio
import sys
import os
from railway_database import RailwayDatabaseManager
from fleet_report_formatter import FleetReportFormatter

async def test_fleet_display():
    """Test fleet report with real group names"""
    try:
        db = RailwayDatabaseManager()
        formatter = FleetReportFormatter(db)
        
        print("Generating fleet report with updated group associations...")
        report = await formatter.format_comprehensive_fleet_report(6, 2025)
        
        print("FLEET REPORT:")
        print("=" * 60)
        print(report)
        print("=" * 60)
        
        # Check for expected group names
        if "Fenny_私人倉庫" in report:
            print("✓ Fenny_私人倉庫 group name found")
        if "Fammy私人助理" in report:
            print("✓ Fammy私人助理 group name found")
            
        # Check USDT calculations
        if "65,203" in report or "65203" in report:
            print("✓ Correct Taiwan USDT total")
        if "4.1" in report:
            print("✓ Correct China USDT total")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fleet_display())