#!/usr/bin/env python3
"""
Test script to verify the new database schema is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.db.database import execute_query

def test_tables():
    """Test that all tables have data."""
    tables = [
        ('regions', 'SELECT COUNT(*) as count FROM regions'),
        ('categories', 'SELECT COUNT(*) as count FROM categories'), 
        ('sales_reps', 'SELECT COUNT(*) as count FROM sales_reps'),
        ('customers', 'SELECT COUNT(*) as count FROM customers'),
        ('products', 'SELECT COUNT(*) as count FROM products'),
        ('orders', 'SELECT COUNT(*) as count FROM orders'),
        ('order_items', 'SELECT COUNT(*) as count FROM order_items'),
    ]
    
    print("🗄️  Database Table Verification")
    print("=" * 40)
    
    for table_name, query in tables:
        try:
            result = execute_query(query)
            count = result[0]['count'] if result else 0
            print(f"{table_name:12} | {count:3} records")
        except Exception as e:
            print(f"{table_name:12} | ERROR: {str(e)}")
    
    print("\n🔍 Sample Data Queries")
    print("=" * 40)
    
    # Test some sample queries
    sample_queries = [
        ("Sales Reps", "SELECT first_name, last_name FROM sales_reps LIMIT 3"),
        ("Categories", "SELECT name, margin_percentage FROM categories"),
        ("Products", "SELECT name, unit_price FROM products LIMIT 5"),
        ("Recent Orders", "SELECT id, order_date, status FROM orders ORDER BY order_date DESC LIMIT 3"),
    ]
    
    for desc, query in sample_queries:
        try:
            result = execute_query(query)
            print(f"\n{desc}:")
            for row in result:
                print(f"  {row}")
        except Exception as e:
            print(f"\n{desc}: ERROR - {str(e)}")

def test_joins():
    """Test complex join queries."""
    print("\n🔗 Join Query Tests")
    print("=" * 40)
    
    join_queries = [
        ("Sales Rep with Region", """
            SELECT sr.first_name, sr.last_name, r.name as region 
            FROM sales_reps sr 
            JOIN regions r ON sr.region_id = r.id 
            LIMIT 3
        """),
        ("Products with Categories", """
            SELECT p.name, c.name as category, p.unit_price 
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            LIMIT 5
        """),
        ("Orders with Customer Info", """
            SELECT o.id, c.first_name, c.last_name, c.company, o.order_date 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.id 
            LIMIT 3
        """),
    ]
    
    for desc, query in join_queries:
        try:
            result = execute_query(query)
            print(f"\n{desc}:")
            for row in result:
                print(f"  {row}")
        except Exception as e:
            print(f"\n{desc}: ERROR - {str(e)}")

if __name__ == "__main__":
    test_tables()
    test_joins()
    print("\n✅ Database schema verification complete!")
