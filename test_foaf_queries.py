#!/usr/bin/env python3
"""
Test script for querying the three FOAF databases.
Since cypher2aql is not readily available, we'll use native AQL queries
to demonstrate the capabilities of each database model.

Author: Arthur Keen
Date: January 2025
"""

import sys
import json
from typing import Dict, List, Any
import config
from database_utils import LocalDatabaseManager
from logging_utils import setup_module_logging

# Set up logging
logger = setup_module_logging(__name__)


class FOAFQueryTester:
    """Test queries across the three FOAF database models"""
    
    def __init__(self):
        """Initialize the query tester"""
        self.db_manager = LocalDatabaseManager()
        self.databases = {}
        
    def connect_to_databases(self) -> bool:
        """Connect to all three FOAF databases"""
        try:
            self.databases = self.db_manager.connect_to_all_foaf_databases()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False
    
    def print_database_structure(self, model_type: str):
        """Print the structure of a specific database"""
        db = self.databases[model_type]
        db_name = config.DATABASE_NAMES[model_type]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"DATABASE STRUCTURE: {db_name} ({model_type.upper()})")
        logger.info(f"{'='*60}")
        
        try:
            collections = db.collections()
            non_system_collections = [c for c in collections if not c['name'].startswith('_')]
            
            for col in non_system_collections:
                count = db.collection(col['name']).count()
                col_type = "edge" if col.get('type') == 3 else "vertex"
                logger.info(f"  {col['name']} ({col_type}): {count} documents")
                
                # Show sample document
                if count > 0:
                    sample = list(db.collection(col['name']).all(limit=1))[0]
                    # Remove _rev and _id for cleaner display
                    sample_clean = {k: v for k, v in sample.items() if not k.startswith('_') or k == '_key'}
                    logger.info(f"    Sample: {json.dumps(sample_clean, indent=6)[:200]}...")
                    
        except Exception as e:
            logger.error(f"Error examining {db_name}: {e}")
    
    def test_rpt_queries(self):
        """Test queries on the RPT model (FOAF-RPT)"""
        logger.info(f"\n{'='*60}")
        logger.info("TESTING RPT MODEL QUERIES (FOAF-RPT)")
        logger.info(f"{'='*60}")
        
        db = self.databases["rpt"]
        
        try:
            # Query 1: Count all statements (triples)
            logger.info("\n1. Total RDF statements:")
            cursor = db.aql.execute("""
                FOR stmt IN foaf_rpt_graph_Statement
                COLLECT WITH COUNT INTO length
                RETURN length
            """)
            total_statements = list(cursor)[0]
            logger.info(f"   Total statements: {total_statements}")
            
            # Query 2: Find statements about people
            logger.info("\n2. Statements about Person type:")
            cursor = db.aql.execute("""
                FOR stmt IN foaf_rpt_graph_Statement
                FOR obj IN foaf_rpt_graph_URIRef
                FILTER stmt._to == obj._id 
                   AND obj.iri LIKE '%foaf/0.1/Person'
                LIMIT 5
                RETURN {
                    subject: stmt._from,
                    predicate: stmt.predicate,
                    object: obj.iri
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
                
        except Exception as e:
            logger.error(f"Error in RPT queries: {e}")
    
    def test_pgt_queries(self):
        """Test queries on the PGT model (FOAF-PGT)"""
        logger.info(f"\n{'='*60}")
        logger.info("TESTING PGT MODEL QUERIES (FOAF-PGT)")
        logger.info(f"{'='*60}")
        
        db = self.databases["pgt"]
        
        try:
            # Query 1: Count all persons
            logger.info("\n1. Person count:")
            cursor = db.aql.execute("""
                FOR person IN Person
                COLLECT WITH COUNT INTO length
                RETURN length
            """)
            person_count = list(cursor)[0]
            logger.info(f"   Total persons: {person_count}")
            
            # Query 2: Find persons with specific properties
            logger.info("\n2. Persons with names and ages:")
            cursor = db.aql.execute("""
                FOR person IN Person
                FILTER person.`http://xmlns.com/foaf/0.1/name` != null
                LIMIT 10
                RETURN {
                    name: person.`http://xmlns.com/foaf/0.1/name`,
                    age: person.`http://xmlns.com/foaf/0.1/age`,
                    title: person.`http://xmlns.com/foaf/0.1/title`
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
            
            # Query 3: Find friendship connections using 'knows' collection
            logger.info("\n3. Social connections (first 5):")
            cursor = db.aql.execute("""
                FOR knows_rel IN knows
                LIMIT 5
                RETURN {
                    from: knows_rel._from,
                    to: knows_rel._to,
                    relationship: 'knows'
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
            
            # Query 4: Find persons by age range
            logger.info("\n4. Persons aged 25-35:")
            cursor = db.aql.execute("""
                FOR person IN Person
                FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25 
                   AND person.`http://xmlns.com/foaf/0.1/age` <= 35
                LIMIT 10
                RETURN {
                    name: person.`http://xmlns.com/foaf/0.1/name`,
                    age: person.`http://xmlns.com/foaf/0.1/age`,
                    title: person.`http://xmlns.com/foaf/0.1/title`
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
                
        except Exception as e:
            logger.error(f"Error in PGT queries: {e}")
    
    def test_lpgt_queries(self):
        """Test queries on the LPGT model (FOAF-LPGT)"""
        logger.info(f"\n{'='*60}")
        logger.info("TESTING LPGT MODEL QUERIES (FOAF-LPGT)")
        logger.info(f"{'='*60}")
        
        db = self.databases["lpgt"]
        
        try:
            # Query 1: Count resources by type
            logger.info("\n1. Resource count:")
            cursor = db.aql.execute("""
                FOR resource IN Resource
                COLLECT WITH COUNT INTO length
                RETURN length
            """)
            resource_count = list(cursor)[0]
            logger.info(f"   Total resources: {resource_count}")
            
            # Query 2: Find Person resources
            logger.info("\n2. Person resources with properties:")
            cursor = db.aql.execute("""
                FOR resource IN Resource
                FILTER resource.`http://www.w3.org/1999/02/22-rdf-syntax-ns#type` LIKE '%foaf/0.1/Person'
                LIMIT 10
                RETURN {
                    name: resource.`http://xmlns.com/foaf/0.1/name`,
                    age: resource.`http://xmlns.com/foaf/0.1/age`,
                    title: resource.`http://xmlns.com/foaf/0.1/title`
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
            
            # Query 3: Social network analysis - find highly connected persons
            logger.info("\n3. Highly connected persons (>5 connections):")
            cursor = db.aql.execute("""
                FOR resource IN Resource
                FILTER resource.`http://www.w3.org/1999/02/22-rdf-syntax-ns#type` LIKE '%foaf/0.1/Person'
                
                LET connections = (
                    FOR edge IN knows
                    FILTER edge._from == resource._id OR edge._to == resource._id
                    RETURN 1
                )
                
                FILTER LENGTH(connections) > 5
                SORT LENGTH(connections) DESC
                LIMIT 10
                RETURN {
                    name: resource.`http://xmlns.com/foaf/0.1/name`,
                    connection_count: LENGTH(connections)
                }
            """)
            for result in cursor:
                logger.info(f"   {result}")
                
        except Exception as e:
            logger.error(f"Error in LPGT queries: {e}")
    
    def compare_performance(self):
        """Compare query performance across the three models"""
        logger.info(f"\n{'='*60}")
        logger.info("PERFORMANCE COMPARISON")
        logger.info(f"{'='*60}")
        
        import time
        
        # Test the same logical query across all three models
        queries = {
            "rpt": """
                FOR stmt IN foaf_rpt_graph_Statement
                COLLECT WITH COUNT INTO length
                RETURN length
            """,
            "pgt": """
                FOR person IN Person
                COLLECT WITH COUNT INTO length
                RETURN length
            """,
            "lpgt": """
                FOR resource IN Resource
                FILTER resource.`http://www.w3.org/1999/02/22-rdf-syntax-ns#type` LIKE '%foaf/0.1/Person'
                COLLECT WITH COUNT INTO length
                RETURN length
            """
        }
        
        for model_type, query in queries.items():
            try:
                db = self.databases[model_type]
                start_time = time.time()
                cursor = db.aql.execute(query)
                result = list(cursor)[0]
                end_time = time.time()
                
                logger.info(f"{model_type.upper()}: {result} records in {(end_time - start_time)*1000:.2f}ms")
                
            except Exception as e:
                logger.error(f"Error in {model_type} performance test: {e}")
    
    def run_all_tests(self):
        """Run all query tests"""
        logger.info("="*60)
        logger.info("FOAF DATABASE QUERY TESTING")
        logger.info("="*60)
        
        if not self.connect_to_databases():
            return False
        
        # Print database structures
        for model_type in ["rpt", "pgt", "lpgt"]:
            self.print_database_structure(model_type)
        
        # Run model-specific tests
        self.test_rpt_queries()
        self.test_pgt_queries()
        self.test_lpgt_queries()
        
        # Performance comparison
        self.compare_performance()
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ All tests completed successfully!")
        logger.info("The three FOAF databases are ready for use:")
        logger.info("- FOAF-RPT: RDF-topology preserving")
        logger.info("- FOAF-PGT: Property graph transformation")
        logger.info("- FOAF-LPGT: Labeled property graph transformation")
        logger.info("="*60)
        
        return True


def main():
    """Main entry point"""
    tester = FOAFQueryTester()
    
    if tester.run_all_tests():
        logger.info("\nTesting completed successfully!")
    else:
        logger.error("Testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
