#!/usr/bin/env python3
"""
Live Interactive Demo for ArangoRDF FOAF Presentation

Perfect for customer demonstrations - step through queries interactively.
"""

import time
from arango import ArangoClient
import config

class LiveDemo:
    def __init__(self):
        self.client = ArangoClient(hosts="http://localhost:8529")
        self.rpt_db = self.client.db("FOAF-RPT", username="root", password="openSesame")
        self.pgt_db = self.client.db("FOAF-PGT", username="root", password="openSesame")
        
    def wait_for_enter(self, message="Press Enter to continue..."):
        input(f"\n🎯 {message}")
        
    def print_header(self, title):
        print("\n" + "="*70)
        print(f"🚀 {title}")
        print("="*70)
        
    def print_query(self, description, query):
        print(f"\n📋 {description}")
        print("-" * 50)
        print("AQL Query:")
        print(query)
        print("-" * 50)
        
    def execute_and_show(self, db, query, description, limit=5):
        self.print_query(description, query)
        self.wait_for_enter("Execute this query?")
        
        try:
            start_time = time.time()
            cursor = db.aql.execute(query)
            results = list(cursor)
            execution_time = time.time() - start_time
            
            print(f"✅ Query executed in {execution_time:.3f} seconds")
            print(f"📊 Results: {len(results)} documents")
            
            if results:
                print("\n🔍 Sample Results:")
                for i, result in enumerate(results[:limit]):
                    print(f"  {i+1}: {result}")
                if len(results) > limit:
                    print(f"  ... and {len(results) - limit} more results")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def demo_database_overview(self):
        self.print_header("DATABASE OVERVIEW - Three Models from Same Data")
        
        print("🗄️  We've loaded the same FOAF data into three different models:")
        print("   1. FOAF-RPT: RDF-Topology Preserving (preserves RDF structure)")
        print("   2. FOAF-PGT: Property Graph Transformation (optimized for queries)")
        print("   3. FOAF-PGT-Node: Alternative approach (unified querying)")
        
        print("\n📈 Model Comparison:")
        for model_type, db_name in config.DATABASE_NAMES.items():
            db = self.client.db(db_name, username="root", password="openSesame")
            collections = db.collections()
            total_docs = sum(db.collection(c['name']).count() 
                           for c in collections if not c['name'].startswith('_'))
            print(f"   {db_name}: {total_docs:,} total documents")
        
        self.wait_for_enter("Ready to explore the queries?")
    
    def demo_pgt_basic_queries(self):
        self.print_header("PGT MODEL - Basic Property Queries")
        
        # Query 1: Count persons
        self.execute_and_show(
            self.pgt_db,
            "RETURN LENGTH(Person)",
            "Count total number of persons in the database"
        )
        
        # Query 2: Find sample persons
        query = '''FOR person IN Person
RETURN {
    name: person.`http://xmlns.com/foaf/0.1/name`,
    age: person.`http://xmlns.com/foaf/0.1/age`,
    title: person.`http://xmlns.com/foaf/0.1/title`
}'''
        self.execute_and_show(
            self.pgt_db,
            query,
            "Get person details with name, age, and job title",
            limit=3
        )
    
    def demo_pgt_filtering(self):
        self.print_header("PGT MODEL - Advanced Filtering")
        
        # Age-based filtering
        query = '''FOR person IN Person
FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25
FILTER person.`http://xmlns.com/foaf/0.1/age` <= 35
RETURN {
    name: person.`http://xmlns.com/foaf/0.1/name`,
    age: person.`http://xmlns.com/foaf/0.1/age`,
    title: person.`http://xmlns.com/foaf/0.1/title`
}'''
        self.execute_and_show(
            self.pgt_db,
            query,
            "Find people aged 25-35 (demographic filtering)",
            limit=5
        )
        
        # Title-based filtering  
        query = '''FOR person IN Person
FILTER person.`http://xmlns.com/foaf/0.1/title` LIKE "%Manager%"
RETURN {
    name: person.`http://xmlns.com/foaf/0.1/name`,
    title: person.`http://xmlns.com/foaf/0.1/title`,
    age: person.`http://xmlns.com/foaf/0.1/age`
}'''
        self.execute_and_show(
            self.pgt_db,
            query,
            "Find all managers (text pattern matching)",
            limit=5
        )
    
    def demo_graph_traversal(self):
        self.print_header("PGT MODEL - Graph Traversal (Social Network)")
        
        # Simple graph traversal
        query = '''FOR person IN Person
LIMIT 1
FOR friend IN 1..1 OUTBOUND person knows
RETURN {
    person: person.`http://xmlns.com/foaf/0.1/name`,
    friend: friend.`http://xmlns.com/foaf/0.1/name`,
    person_title: person.`http://xmlns.com/foaf/0.1/title`,
    friend_title: friend.`http://xmlns.com/foaf/0.1/title`
}'''
        self.execute_and_show(
            self.pgt_db,
            query,
            "Find direct friends (1-hop graph traversal)",
            limit=3
        )
        
        # Multi-hop traversal
        query = '''FOR person IN Person
FILTER person.`http://xmlns.com/foaf/0.1/name` != null
LIMIT 1
FOR friend IN 2..2 OUTBOUND person knows
RETURN {
    start_person: person.`http://xmlns.com/foaf/0.1/name`,
    friend_of_friend: friend.`http://xmlns.com/foaf/0.1/name`,
    connection_type: "2-hop connection"
}'''
        self.execute_and_show(
            self.pgt_db,
            query,
            "Find friends-of-friends (2-hop graph traversal)",
            limit=3
        )
    
    def demo_rpt_model(self):
        self.print_header("RPT MODEL - RDF Triple Store Queries")
        
        # Count statements
        self.execute_and_show(
            self.rpt_db,
            "RETURN LENGTH(foaf_rpt_graph_Statement)",
            "Count total RDF statements (triples) in the knowledge graph"
        )
        
        # Browse RDF structure
        query = '''FOR stmt IN foaf_rpt_graph_Statement
RETURN {
    subject: stmt._from,
    predicate: stmt.`rdf-type`,
    object: stmt._to
}'''
        self.execute_and_show(
            self.rpt_db,
            query,
            "Browse RDF triples (subject-predicate-object structure)",
            limit=5
        )
    
    def demo_performance_comparison(self):
        self.print_header("PERFORMANCE & MODEL COMPARISON")
        
        print("🏁 Performance Comparison:")
        
        # PGT person count (optimized)
        start_time = time.time()
        pgt_count = list(self.pgt_db.aql.execute("RETURN LENGTH(Person)"))[0]
        pgt_time = time.time() - start_time
        
        # RPT statement count
        start_time = time.time()
        rpt_count = list(self.rpt_db.aql.execute("RETURN LENGTH(foaf_rpt_graph_Statement)"))[0]
        rpt_time = time.time() - start_time
        
        print(f"   📊 PGT Person Count: {pgt_count:,} in {pgt_time:.3f}s")
        print(f"   📊 RPT Triple Count: {rpt_count:,} in {rpt_time:.3f}s")
        
        print("\n🎯 Key Advantages:")
        print("   ✅ Native AQL queries (no SPARQL translation needed)")
        print("   ✅ Multiple modeling approaches for different use cases")
        print("   ✅ High-performance graph traversals")
        print("   ✅ Seamless integration with existing ArangoDB infrastructure")
        
        self.wait_for_enter("Demo complete!")
    
    def run_full_demo(self):
        print("🎉 Welcome to the ArangoRDF FOAF Live Demonstration!")
        print("📋 This demo shows how to query RDF data in ArangoDB using AQL")
        
        self.demo_database_overview()
        self.demo_pgt_basic_queries()
        self.demo_pgt_filtering()
        self.demo_graph_traversal()
        self.demo_rpt_model()
        self.demo_performance_comparison()
        
        print("\n🎉 Thank you for attending the ArangoRDF demonstration!")
        print("📧 Questions? Contact: Arthur Keen")
        print("🌐 Code: https://github.com/ArthurKeen/arangoRDF-FOAF-Demo")

def main():
    demo = LiveDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main() 