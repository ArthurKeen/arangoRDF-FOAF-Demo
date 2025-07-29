#!/usr/bin/env python3
"""
ArangoRDF FOAF Demonstration Script

This script demonstrates loading FOAF (Friend of a Friend) RDF data into ArangoDB
using three different graph models:
1. RPT (RDF-Topology Preserving Transformation)
2. PGT (Property Graph Transformation)
3. PGT-Node (Property Graph with single vertex collection)

Author: Arthur Keen
Date: January 2025
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Optional

from rdflib import Graph
from arango import ArangoClient
from arango_rdf import ArangoRDF
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FOAFDemo:
    """Main demonstration class for FOAF RDF data loading"""
    
    def __init__(self, use_cloud: bool = False):
        """Initialize the demo with local or cloud configuration"""
        self.use_cloud = use_cloud
        self.db_config = config.CLOUD_CONFIG if use_cloud else config.LOCAL_CONFIG
        self.client = None
        self.sys_db = None
        self.databases = {}
        self.arango_rdf_instances = {}
        
    def connect_to_arango(self) -> bool:
        """Connect to ArangoDB and set up system database"""
        try:
            logger.info(f"Connecting to ArangoDB at {self.db_config['host']}")
            self.client = ArangoClient(hosts=self.db_config["host"])
            
            self.sys_db = self.client.db(
                "_system",
                username=self.db_config["username"],
                password=self.db_config["password"]
            )
            
            # Test connection
            self.sys_db.version()
            logger.info("Successfully connected to ArangoDB")
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
                
                # Drop existing database if it exists
                if self.sys_db.has_database(db_name):
                    logger.info(f"Dropping existing database: {db_name}")
                    self.sys_db.delete_database(db_name)
                
                # Create new database
                self.sys_db.create_database(db_name)
                
                # Connect to the new database
                db = self.client.db(
                    db_name,
                    username=self.db_config["username"],
                    password=self.db_config["password"]
                )
                
                self.databases[model_type] = db
                self.arango_rdf_instances[model_type] = ArangoRDF(db)
                
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
    
    def load_pgt_node_model(self, foaf_graph: Graph) -> bool:
        """Load data using PGT with single vertex collection named 'node'"""
        try:
            logger.info("Loading data using PGT-Node model...")
            arango_rdf = self.arango_rdf_instances["pgt_node"]
            
            # PGT model with single Node collection for all vertices
            arango_rdf.rdf_to_arangodb_by_pgt(
                name=config.GRAPH_NAMES["pgt_node"],
                rdf_graph=foaf_graph,
                overwrite_graph=True,
                resource_collection_name="Node"  # This will put all vertices in a "Node" collection
            )
            
            logger.info("PGT-Node model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PGT-Node model: {e}")
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
                vertex_collections = [c for c in collections if not c['name'].startswith('_') and not c['name'].endswith('_edge')]
                edge_collections = [c for c in collections if c['name'].endswith('_edge') or c['type'] == 3]
                
                logger.info(f"Vertex Collections: {len(vertex_collections)}")
                for col in vertex_collections:
                    count = db.collection(col['name']).count()
                    logger.info(f"  - {col['name']}: {count} documents")
                
                logger.info(f"Edge Collections: {len(edge_collections)}")
                for col in edge_collections:
                    count = db.collection(col['name']).count()
                    logger.info(f"  - {col['name']}: {count} documents")
                    
            except Exception as e:
                logger.error(f"Error getting stats for {db_name}: {e}")
    
    def run_demo(self) -> bool:
        """Run the complete demonstration"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("ARANGORDF FOAF DEMONSTRATION")
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
        
        # Step 6: Load data into PGT-Node model
        if not self.load_pgt_node_model(foaf_graph):
            return False
        
        # Step 7: Print statistics
        self.print_database_stats()
        
        elapsed_time = time.time() - start_time
        logger.info(f"\nDemo completed successfully in {elapsed_time:.2f} seconds")
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArangoRDF FOAF Demonstration")
    parser.add_argument(
        "--cloud", 
        action="store_true", 
        help="Use cloud ArangoDB instance instead of local"
    )
    
    args = parser.parse_args()
    
    if args.cloud and not config.CLOUD_CONFIG["password"]:
        logger.error("Cloud password not set. Please set ARANGO_CLOUD_PASSWORD environment variable.")
        sys.exit(1)
    
    demo = FOAFDemo(use_cloud=args.cloud)
    
    if demo.run_demo():
        logger.info("\nDemo completed successfully!")
        logger.info("You can now run AQL queries using query_demo.py")
    else:
        logger.error("Demo failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 