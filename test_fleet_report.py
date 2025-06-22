#!/usr/bin/env python3
"""
Test script to verify fleet report USDT calculations and group name display
"""
import asyncio
import os
from railway_database import RailwayDatabaseManager
from fleet_report_formatter import FleetReportFormatter

async def test_fleet_report():
    """Test the corrected fleet report functionality"""
    try:
        # Initialize database and formatter
        db = RailwayDatabaseManager()
        formatter = FleetReportFormatter(db)
        
        print("Testing fleet report for June 2025...")
        print("=" * 60)
        
        # Generate fleet report
        report = await formatter.format_comprehensive_fleet_report(6, 2025)
        
        print("FLEET REPORT OUTPUT:")
        print("-" * 40)
        print(report)
        print("-" * 40)
        
        # Verify expected USDT calculations
        print("\nExpected USDT calculations:")
        print("Taiwan: 30,003.00 + 35,200.00 = 65,203.00 USDT")
        print("China: 1.33 + 2.77 = 4.11 USDT")
        
        # Check if report contains correct values
        if "65,203.00" in report:
            print("✓ Taiwan USDT calculation is CORRECT")
        else:
            print("✗ Taiwan USDT calculation is INCORRECT")
            
        if "4.1" in report:
            print("✓ China USDT calculation is CORRECT")
        else:
            print("✗ China USDT calculation is INCORRECT")
            
        # Check for group name display
        if "<code>北金國際" in report:
            print("✓ Group name formatting is CORRECT")
        else:
            print("✗ Group name formatting needs attention")
            
    except Exception as e:
        print(f"Error testing fleet report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fleet_report())