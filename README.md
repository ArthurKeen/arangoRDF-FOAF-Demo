# ArangoRDF FOAF Demonstration

A comprehensive demonstration of the ArangoRDF Python library showcasing three different graph models for FOAF (Friend of a Friend) data in ArangoDB.

## Overview

This project demonstrates how to load RDF data into ArangoDB using three different transformation approaches:

1. **RPT (RDF-Topology Preserving Transformation)** - Preserves the original RDF graph structure
2. **PGT (Property Graph Transformation)** - Converts datatype properties to document properties  
3. **LPGT (Labeled Property Graph Transformation)** - Single vertex collection ("Node") and single edge collection ("relation") with simplified property names

## Features

- 🗄️ **Three Database Models**: Compare different approaches to storing RDF data
- 🔍 **Comprehensive AQL Queries**: Extensive query examples for each model
- ☁️ **Multi-Environment Support**: Works with local and cloud ArangoDB instances
- 📊 **Statistics & Analytics**: Database statistics and performance comparisons
- 🚀 **Easy Setup**: Automated database creation and data loading

## Prerequisites

- Python 3.9+
- ArangoDB 3.11+ (local Docker instance or cloud)
- FOAF data files (included in your `~/data/semantics/foaf/` directory)

## Installation

1. **Clone/Navigate to the project directory:**
   ```bash
   cd ~/code/semanticlayer/foafdemo
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (for cloud deployment):**
   ```bash
   export ARANGO_CLOUD_PASSWORD="your_cloud_password_here"
   ```

## Quick Start

### Local Deployment

Ensure your local ArangoDB is running on Docker:
```bash
docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=openSesame arangodb/arangodb:latest
```

**Load FOAF Data into All Three Models:**
```bash
python setup_foaf_databases.py  # Creates RPT and PGT models
python create_lpgt_manual.py    # Creates LPGT model with proper structure
```

**Test All Databases:**
```bash
python test_foaf_queries.py     # Run test queries against all three models
```

**Run Customer Demo:**
```bash
python customer_demo.py
```

### Cloud Deployment

**Set Cloud Password (not stored in repo):**
```bash
export ARANGO_CLOUD_PASSWORD="your_cloud_password"
```

**Deploy to Cloud:**
```bash
python foaf_demo.py --cloud
```

**Run Cloud Demo:**
```bash
python cloud_demo.py
```

This will:
- Connect to your cloud ArangoDB instance
- Load 300 FOAF persons with ~10,000 RDF triples
- Create three databases: `FOAF-RPT`, `FOAF-PGT`, `FOAF-LPGT`
- Display statistics for each model and run demo queries

## Database Models

### 1. RPT (RDF-Topology Preserving)
- **Database**: `FOAF-RPT`
- **Structure**: Each RDF triple becomes an edge
- **Use Case**: Preserves original RDF semantics
- **Collections**: Vertex collections for subjects/objects, edge collection for predicates

### 2. PGT (Property Graph Transformation)
- **Database**: `FOAF-PGT`
- **Structure**: Datatype properties become document properties
- **Use Case**: Optimized for property-based queries
- **Collections**: Separate collections for different entity types (Person, Organization, etc.)

### 3. LPGT (Labeled Property Graph Transformation)
- **Database**: `FOAF-LPGT`
- **Structure**: Single "Node" collection and single "relation" collection
- **Use Case**: Neo4j-style property graph with simplified property names
- **Collections**: "Node" (all vertices) and "relation" (all edges)
- **Features**: Localname properties (e.g., "name" instead of "http://xmlns.com/foaf/0.1/name")
- **Implementation**: Custom manual transformation (ArangoRDF's built-in LPG method not available in current version)

## Example Queries

### Find People by Age Range (PGT Model)
```aql
FOR person IN Person
FILTER person.`http://xmlns.com/foaf/0.1/age` >= 25 
   AND person.`http://xmlns.com/foaf/0.1/age` <= 35
RETURN {
    name: person.`http://xmlns.com/foaf/0.1/name`,
    age: person.`http://xmlns.com/foaf/0.1/age`,
    title: person.`http://xmlns.com/foaf/0.1/title`
}
```

### Find Friends of Friends (Graph Traversal)
```aql
FOR person IN Person
LIMIT 1
FOR v, e, p IN 2..2 OUTBOUND person._id knows
RETURN {
    start_person: person.`http://xmlns.com/foaf/0.1/name`,
    friend_of_friend: v.`http://xmlns.com/foaf/0.1/name`,
    path_length: LENGTH(p.edges)
}
```

### Find Connected People (LPGT Model with Simplified Properties)
```aql
FOR person IN Node
FILTER person.name != null AND person._rdftype == "URIRef"

LET connections = (
    FOR rel IN relation
    FILTER rel._from == person._id AND rel.predicate_label == "knows"
    FOR friend IN Node
    FILTER friend._id == rel._to
    RETURN friend.name
)

FILTER LENGTH(connections) > 0
RETURN {
    person: person.name,
    knows: connections,
    connection_count: LENGTH(connections)
}
SORT connection_count DESC
```

## Cloud Deployment

To run against the cloud ArangoDB instance:

1. **Set the cloud password:**
   ```bash
   export ARANGO_CLOUD_PASSWORD="your_actual_password"
   ```

2. **Run with cloud flag:**
   ```bash
   python foaf_demo.py --cloud
   python query_demo.py --cloud
   ```

## Project Structure

```
foafdemo/
├── setup_foaf_databases.py   # Creates RPT and PGT databases
├── create_lpgt_manual.py      # Creates LPGT database with proper structure
├── test_foaf_queries.py       # AQL query testing for all models
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Configuration

Edit `config.py` to modify:
- Database connection settings
- Database names
- Data file paths
- Graph names

## Data Sources

The demonstration uses FOAF data located at:
- **Ontology**: `/Users/arthurkeen/data/semantics/foaf/foaf.rdf`
- **Sample Data**: `/Users/arthurkeen/data/semantics/foaf/foaf-data.ttl`

The sample data contains:
- 300 FOAF Person entities
- Properties: name, age, title, email, interests
- Relationships: knows (friendship connections)
- ~8,000 total RDF triples

## Performance Comparison

| Model | Strengths | Use Cases |
|-------|-----------|-----------|
| **RPT** | Preserves RDF semantics, SPARQL-like queries | RDF applications, semantic web |
| **PGT** | Fast property queries, typed collections | Business applications, analytics |
| **LPGT** | Neo4j-style graph, simplified properties, single collections | Graph analysis, network traversals, simplified queries |

## Troubleshooting

### Connection Issues
- Ensure ArangoDB is running on the correct port
- Check username/password credentials
- Verify network connectivity for cloud instances

### Data Loading Errors
- Confirm FOAF data files exist at specified paths
- Check file permissions and format
- Verify sufficient disk space

### Query Failures
- Ensure databases are created and loaded
- Check collection names match the model
- Verify AQL syntax for your ArangoDB version

## Customer Presentation Points

### 1. **Flexibility**
- Multiple ways to model the same RDF data
- Choose the approach that fits your use case
- Easy migration between models

### 2. **Performance**
- Native AQL queries (faster than SPARQL translation)
- Optimized for different query patterns
- Scalable graph traversals

### 3. **Integration**
- Works with existing ArangoDB infrastructure
- Leverages ArangoDB's multi-model capabilities
- Standard Python libraries and tools

### 4. **Real-world Data**
- 300 person social network
- Realistic relationships and properties  
- Demonstrates scalability potential

### Demo Scripts Available:
- `customer_demo.py` - Perfect for customer presentations (local)
- `cloud_demo.py` - Cloud deployment demonstration
- `live_demo.py` - Interactive step-by-step presentation format
- `simple_queries.py` - Basic working query examples

## License

This demonstration project is for educational and customer presentation purposes.

## Contact

- **Author**: Arthur Keen
- **Date**: January 2025
- **Purpose**: Customer demonstration of ArangoRDF capabilities 