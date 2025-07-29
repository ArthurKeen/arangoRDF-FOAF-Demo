"""
Configuration file for ArangoRDF FOAF Demonstration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local ArangoDB Configuration
LOCAL_CONFIG = {
    "host": "http://localhost:8529",
    "username": "root",
    "password": "openSesame",
    "database_prefix": "FOAF"
}

# Cloud ArangoDB Configuration
CLOUD_CONFIG = {
    "host": "https://arangodb-platform-qa.pilot.arangodb.com/",
    "username": "root",
    "password": os.getenv("ARANGO_CLOUD_PASSWORD", ""),  # Set via environment variable
    "database_prefix": "FOAF"
}

# Database names for the three models
DATABASE_NAMES = {
    "rpt": "FOAF-RPT",
    "pgt": "FOAF-PGT", 
    "pgt_node": "FOAF-PGT-Node"
}

# Data file paths
DATA_PATHS = {
    "foaf_ontology": "~/data/semantics/foaf/foaf.rdf",
    "foaf_data": "~/data/semantics/foaf/foaf-data.ttl"
}

# Graph names
GRAPH_NAMES = {
    "rpt": "foaf_rpt_graph",
    "pgt": "foaf_pgt_graph",
    "pgt_node": "foaf_pgt_node_graph"
} 