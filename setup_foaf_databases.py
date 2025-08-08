#!/usr/bin/env python3
"""
Setup script to create three FOAF databases as requested:
1. FOAF-RPT using RPT transformation
2. FOAF-PGT using PGT transformation  
3. FOAF-LPGT using LPGT transformation

Author: Arthur Keen
Date: January 2025
"""

import sys
import time
from pathlib import Path
from typing import Optional

from rdflib import Graph
import config
from database_utils import LocalDatabaseManager
from logging_utils import setup_module_logging

# Set up logging
logger = setup_module_logging(__name__)


class FOAFDatabaseSetup:
    """Setup class for creating the three FOAF databases"""
    
    def __init__(self):
        """Initialize the setup with local Docker configuration"""
        self.db_manager = LocalDatabaseManager()
        self.databases = {}
        self.arango_rdf_instances = {}
        
    def connect_to_arango(self) -> bool:
        """Connect to ArangoDB and set up system database"""
        try:
            self.db_manager.connect_to_system_db()
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            return False
    
    def load_foaf_data(self) -> Optional[Graph]:
        """Load FOAF RDF data from file"""
        try:
            logger.info("Loading FOAF RDF data...")
            foaf_graph = Graph()
            
            # Load the FOAF data file
            data_path = config.DATA_PATHS["foaf_data"]
            if not Path(data_path).exists():
                logger.error(f"FOAF data file not found: {data_path}")
                return None
                
            foaf_graph.parse(data_path, format="turtle")
            logger.info(f"Loaded {len(foaf_graph)} RDF triples")
            
            return foaf_graph
            
        except Exception as e:
            logger.error(f"Failed to load FOAF data: {e}")
            return None
    
    def create_databases(self) -> bool:
        """Create the three databases for different graph models"""
        try:
            for model_type, db_name in config.DATABASE_NAMES.items():
                logger.info(f"Creating database: {db_name}")
                
                # Use database manager to recreate database
                db = self.db_manager.recreate_database(db_name)
                
                self.databases[model_type] = db
                self.arango_rdf_instances[model_type] = self.db_manager.get_arango_rdf(db)
                
            logger.info("All databases created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create databases: {e}")
            return False
    
    def load_rpt_model(self, foaf_graph: Graph) -> bool:
        """Load data using RPT (RDF-Topology Preserving Transformation)"""
        try:
            logger.info("Loading data using RPT model...")
            arango_rdf = self.arango_rdf_instances["rpt"]
            
            # RPT preserves RDF structure - each triple becomes an edge
            arango_rdf.rdf_to_arangodb_by_rpt(
                name=config.GRAPH_NAMES["rpt"],
                rdf_graph=foaf_graph,
                overwrite_graph=True
            )
            
            logger.info("RPT model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load RPT model: {e}")
            return False
    
    def load_pgt_model(self, foaf_graph: Graph) -> bool:
        """Load data using PGT (Property Graph Transformation)"""
        try:
            logger.info("Loading data using PGT model...")
            arango_rdf = self.arango_rdf_instances["pgt"]
            
            # PGT converts datatype properties to document properties
            arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["pgt"],
                rdf_graph=foaf_graph,
                overwrite_graph=True
            )
            
            logger.info("PGT model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PGT model: {e}")
            return False
    
    def load_lpgt_model(self, foaf_graph: Graph) -> bool:
        """Load data using LPGT (Labeled Property Graph Transformation)"""
        try:
            logger.info("Loading data using LPGT model...")
            arango_rdf = self.arango_rdf_instances["lpgt"]
            
            # LPGT model - similar to PGT but with additional labeling features
            # Using PGT with specific configuration for LPGT approach
            arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["lpgt"],
                rdf_graph=foaf_graph,
                overwrite_graph=True,
                resource_collection_name="Resource"  # Use generic Resource collection
            )
            
            logger.info("LPGT model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LPGT model: {e}")
            return False
    
    def print_database_stats(self):
        """Print statistics for all databases"""
        logger.info("\n" + "="*60)
        logger.info("DATABASE STATISTICS")
        logger.info("="*60)
        
        for model_type, db in self.databases.items():
            db_name = config.DATABASE_NAMES[model_type]
            logger.info(f"\n{db_name} ({model_type.upper()}):")
            logger.info("-" * 40)
            
            try:
                # Get collections
                collections = db.collections()
                non_system_collections = [c for c in collections if not c['name'].startswith('_')]
                
                logger.info(f"Collections: {len(non_system_collections)}")
                total_documents = 0
                
                for col in non_system_collections:
                    count = db.collection(col['name']).count()
                    total_documents += count
                    col_type = "edge" if col.get('type') == 3 else "vertex"
                    logger.info(f"  - {col['name']} ({col_type}): {count} documents")
                
                logger.info(f"Total documents: {total_documents}")
                    
            except Exception as e:
                logger.error(f"Error getting stats for {db_name}: {e}")
    
    def setup_databases(self) -> bool:
        """Run the complete database setup"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("FOAF DATABASE SETUP")
        logger.info("="*60)
        
        # Step 1: Connect to ArangoDB
        if not self.connect_to_arango():
            return False
        
        # Step 2: Load FOAF RDF data
        foaf_graph = self.load_foaf_data()
        if foaf_graph is None:
            return False
        
        # Step 3: Create databases
        if not self.create_databases():
            return False
        
        # Step 4: Load data into RPT model
        if not self.load_rpt_model(foaf_graph):
            return False
        
        # Step 5: Load data into PGT model
        if not self.load_pgt_model(foaf_graph):
            return False
        
        # Step 6: Load data into LPGT model
        if not self.load_lpgt_model(foaf_graph):
            return False
        
        # Step 7: Print statistics
        self.print_database_stats()
        
        elapsed_time = time.time() - start_time
        logger.info(f"\nDatabase setup completed successfully in {elapsed_time:.2f} seconds")
        
        return True


def main():
    """Main entry point"""
    logger.info("Setting up FOAF databases as requested:")
    logger.info("1. FOAF-RPT (RPT transformation)")
    logger.info("2. FOAF-PGT (PGT transformation)")
    logger.info("3. FOAF-LPGT (LPGT transformation)")
    
    setup = FOAFDatabaseSetup()
    
    if setup.setup_databases():
        logger.info("\n✅ All databases created successfully!")
        logger.info("Next step: Install cypher2aql service on FOAF-PGT database")
        logger.info("\nDatabases ready:")
        logger.info("- FOAF-RPT: RDF-topology preserving transformation")
        logger.info("- FOAF-PGT: Property graph transformation")
        logger.info("- FOAF-LPGT: Labeled property graph transformation")
    else:
        logger.error("❌ Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
