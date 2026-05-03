import os
import json
import logging
from memory_engine import MemoryEngine

class MemoryGraph:
    def __init__(self, vault_path: str, graph_path: str):
        self.vault_path = vault_path
        self.graph_path = graph_path
        self.memory = MemoryEngine(vault_path)
        self.graph = {
            "nodes": [],
            "edges": [],
            "core_node": "UsturZ Knowledge Hub"
        }

    def scan_and_build(self):
        """Scans the vault and builds a relational knowledge graph."""
        logging.info("Building Knowledge Graph...")
        
        if not os.path.exists(self.vault_path):
            logging.warning(f"Vault path not found: {self.vault_path}")
            return "Vault path not found."
            
        files = os.listdir(self.vault_path)
        
        # Define concept clusters for the graph
        clusters = {
            "Energy": ["energy", "energetika", "transformer", "sinxron", "power", "quyosh", "электр"],
            "Hydraulics": ["hydraul", "hidravlik", "suv", "oqim", "pressure", "гидравл"],
            "Nuclear": ["atom", "магатэ", "nuclear", "узатом", "ядер", "reactor"],
            "Management": ["policy", "management", "cv", "resume", "staj", "tajriba"],
            "IT/Unity": ["unity", "script", "code", "c#", "build", "python"],
            "Trading": ["trading", "forex", "market", "birja", "crypto", "treyder"],
            "Economics": ["iqtisod", "econom", "moliya", "finance", "bozor"],
            "Physics": ["fizika", "physics", "matematika", "math", "quantum"],
            "Engineering": ["техник", "texnika", "стандарт", "конструкц", "саноат"],
        }

        for file_name in files:
            path = os.path.join(self.vault_path, file_name)
            node_id = file_name
            
            # Identify which clusters this file belongs to
            tags = []
            file_lower = file_name.lower()
            for cluster, keywords in clusters.items():
                if any(k in file_lower for k in keywords):
                    tags.append(cluster)
            
            node = {
                "id": node_id,
                "tags": tags,
                "type": "document"
            }
            self.graph["nodes"].append(node)
            
            # Create edges to core node for relevant files
            if tags:
                self.graph["edges"].append({"from": node_id, "to": self.graph["core_node"], "relation": "supports"})

        self.save_graph()
        return f"Graph built with {len(self.graph['nodes'])} nodes."

    def save_graph(self):
        try:
            with open(self.graph_path, 'w', encoding='utf-8') as f:
                json.dump(self.graph, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving graph data: {e}")

    def get_graph_summary(self):
        if not os.path.exists(self.graph_path):
            self.scan_and_build()
        return json.dumps(self.graph)
