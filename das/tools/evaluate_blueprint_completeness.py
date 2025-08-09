#!/usr/bin/env python3
"""
MVP Blueprint Completeness Evaluator
Compares Charter vs Blueprint using basic heuristics
"""

import os
import re
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

class BlueprintEvaluator:
    """Simple evaluator using rule-based checks"""
    
    def __init__(self, weights_config: str = None):
        # Default weights for each check category
        self.weights = {
            'structural_sections': 0.15,    # Required sections present
            'objectives_coverage': 0.15,    # Objectives → Components  
            'functional_coverage': 0.25,    # Functional reqs → Flows/APIs
            'nfr_coverage': 0.20,          # NFRs → Technical decisions
            'constraints_mapped': 0.15,     # Constraints → ADRs
            'glossary_consistency': 0.10    # Term consistency
        }
        
        if weights_config and Path(weights_config).exists():
            with open(weights_config, 'r') as f:
                custom_weights = yaml.safe_load(f)
                self.weights.update(custom_weights)
    
    def parse_charter(self, charter_dir: str) -> Dict:
        """Extract key information from Charter directory structure"""
        charter_data = {
            'objectives': [],
            'functional_reqs': [],
            'nfr': [],
            'constraints': [],
            'glossary': []
        }
        
        charter_path = Path(charter_dir)
        
        # Read objetivo.md for objectives and requirements
        objetivo_file = charter_path / '03_objetivo.md'
        if objetivo_file.exists():
            content = objetivo_file.read_text(encoding='utf-8')
            charter_data['objectives'] = self._extract_objectives(content)
            charter_data['functional_reqs'] = self._extract_functional_reqs(content)
        
        # Read vision.md for high-level requirements  
        vision_file = charter_path / '04_vision.md'
        if vision_file.exists():
            content = vision_file.read_text(encoding='utf-8')
            charter_data['nfr'] = self._extract_nfr(content)
        
        # Read alcance.md for constraints
        alcance_file = charter_path / '05_alcance.md'  
        if alcance_file.exists():
            content = alcance_file.read_text(encoding='utf-8')
            charter_data['constraints'] = self._extract_constraints(content)
            
        return charter_data
    
    def parse_blueprint(self, blueprint_path: str) -> Dict:
        """Extract key information from Blueprint YAML"""
        with open(blueprint_path, 'r', encoding='utf-8') as f:
            blueprint_data = yaml.safe_load(f)
            
        return {
            'sections': list(blueprint_data.keys()),
            'components': blueprint_data.get('componentes', {}).keys() if 'componentes' in blueprint_data else [],
            'flows': 'flujos_datos_eventos' in blueprint_data,
            'nfr_section': 'seguridad_enforcement' in blueprint_data and 'operaciones' in blueprint_data,
            'decisions': 'decisiones_arquitectonicas' in blueprint_data,
            'glossary_terms': blueprint_data.get('glosario', {}).keys() if 'glosario' in blueprint_data else []
        }
    
    def evaluate_completeness(self, charter_data: Dict, blueprint_data: Dict) -> Tuple[float, Dict]:
        """Run all checks and return weighted score + breakdown"""
        
        checks = {}
        
        # 1. Structural sections check
        required_sections = ['arquitectura', 'componentes', 'flujos_datos_eventos', 
                           'seguridad_enforcement', 'operaciones', 'decisiones_arquitectonicas']
        present_sections = [s for s in required_sections if s in blueprint_data['sections']]
        checks['structural_sections'] = len(present_sections) / len(required_sections)
        
        # 2. Objectives coverage (simple keyword matching)
        objectives_covered = 0
        for obj in charter_data['objectives']:
            if any(self._text_similarity(obj, str(comp)) > 0.3 for comp in blueprint_data['components']):
                objectives_covered += 1
        checks['objectives_coverage'] = objectives_covered / max(len(charter_data['objectives']), 1)
        
        # 3. Functional requirements coverage
        functional_covered = 0
        for req in charter_data['functional_reqs']:
            if blueprint_data['flows']:  # Simple: if flows section exists, assume some coverage
                functional_covered += 0.5
        checks['functional_coverage'] = min(functional_covered / max(len(charter_data['functional_reqs']), 1), 1.0)
        
        # 4. NFR coverage
        checks['nfr_coverage'] = 1.0 if blueprint_data['nfr_section'] else 0.0
        
        # 5. Constraints mapped to decisions
        constraints_mapped = 0
        for constraint in charter_data['constraints']:
            if blueprint_data['decisions']:
                constraints_mapped += 0.8  # Assume good coverage if decisions section exists
        checks['constraints_mapped'] = min(constraints_mapped / max(len(charter_data['constraints']), 1), 1.0)
        
        # 6. Glossary consistency
        charter_terms = set(charter_data['glossary'])
        blueprint_terms = set(blueprint_data['glossary_terms'])
        if charter_terms:
            overlap = len(charter_terms.intersection(blueprint_terms))
            checks['glossary_consistency'] = overlap / len(charter_terms)
        else:
            checks['glossary_consistency'] = 1.0
        
        # Calculate weighted score
        total_score = sum(checks[check] * self.weights[check] for check in checks)
        
        return total_score, checks
    
    def _extract_objectives(self, content: str) -> List[str]:
        """Extract objectives from markdown content"""
        # Look for bullet points or numbered lists
        objectives = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')):
                # Remove list markers
                clean_line = re.sub(r'^[-*]\s*|\d+\.\s*', '', line).strip()
                if len(clean_line) > 10:  # Filter out short lines
                    objectives.append(clean_line)
        
        return objectives
    
    def _extract_functional_reqs(self, content: str) -> List[str]:
        """Extract functional requirements from content"""
        # Similar to objectives but look for different patterns
        reqs = []
        lines = content.split('\n')
        
        in_req_section = False
        for line in lines:
            if 'requisito' in line.lower() or 'funcional' in line.lower():
                in_req_section = True
                continue
            if in_req_section and line.strip().startswith(('- ', '* ')):
                clean_line = re.sub(r'^[-*]\s*', '', line.strip())
                if len(clean_line) > 15:
                    reqs.append(clean_line)
                    
        return reqs
    
    def _extract_nfr(self, content: str) -> List[str]:
        """Extract non-functional requirements"""
        nfr_keywords = ['rendimiento', 'escalabilidad', 'seguridad', 'disponibilidad', 'usabilidad']
        nfr = []
        
        for keyword in nfr_keywords:
            if keyword in content.lower():
                nfr.append(f"Requisito de {keyword}")
                
        return nfr
    
    def _extract_constraints(self, content: str) -> List[str]:
        """Extract constraints and limitations"""
        constraints = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['limitación', 'restricción', 'constraint']):
                constraints.append(line.strip())
                
        return constraints
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

def main():
    parser = argparse.ArgumentParser(description='Evaluate Blueprint completeness vs Charter')
    parser.add_argument('--charter', required=True, help='Path to Charter directory')
    parser.add_argument('--blueprint', required=True, help='Path to Blueprint YAML file')
    parser.add_argument('--weights', help='Path to custom weights YAML file')
    parser.add_argument('--verbose', action='store_true', help='Show detailed breakdown')
    
    args = parser.parse_args()
    
    evaluator = BlueprintEvaluator(args.weights)
    
    # Parse inputs
    charter_data = evaluator.parse_charter(args.charter)
    blueprint_data = evaluator.parse_blueprint(args.blueprint)
    
    # Evaluate
    score, breakdown = evaluator.evaluate_completeness(charter_data, blueprint_data)
    
    # Output results
    print(f"Blueprint Completeness: {score:.2f} ({score*100:.0f}%)")
    
    if args.verbose:
        print("\nDetailed breakdown:")
        for check, value in breakdown.items():
            weight = evaluator.weights[check]
            contribution = value * weight
            print(f"  {check}: {value:.2f} (weight: {weight:.2f}, contribution: {contribution:.3f})")

if __name__ == "__main__":
    main()