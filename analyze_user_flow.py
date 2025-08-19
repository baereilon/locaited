#!/usr/bin/env python
"""
User Flow Pipeline Analyzer - Shows exactly what each agent produces in the actual user flow.
Matches the real user experience with profile building from CSV.
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.fact_checker import FactCheckerAgent
from agents.publisher import PublisherAgent
from agents.workflow import WorkflowState, create_workflow

class UserFlowAnalyzer:
    """Analyze the complete user flow with full visibility."""
    
    def __init__(self, output_dir: str = None):
        """Initialize analyzer with output directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir or f"user_flow_analysis_{timestamp}")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def save_csv(self, data: List[Dict], filename: str, cycle: int = 1):
        """Save data to CSV in the appropriate cycle folder."""
        cycle_dir = self.output_dir / f"cycle_{cycle}"
        cycle_dir.mkdir(exist_ok=True)
        
        filepath = cycle_dir / filename
        if not data:
            # Save empty file with headers only
            with open(filepath, 'w') as f:
                f.write("No data\n")
            return
            
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"[Saved to: {filepath}]")
    
    def save_json(self, data: Any, filename: str, cycle: int = None):
        """Save data to JSON."""
        if cycle:
            cycle_dir = self.output_dir / f"cycle_{cycle}"
            cycle_dir.mkdir(exist_ok=True)
            filepath = cycle_dir / filename
        else:
            filepath = self.output_dir / filename
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def analyze_editor(self, query: str, cycle: int = 1) -> Dict:
        """Analyze Editor agent output."""
        print("\nEDITOR - PROFILE BUILDING:")
        print("="*60)
        
        agent = EditorAgent()
        
        # Build profile from CSV
        print("Loading user history from: test data/Liri Interesting events.csv")
        profile = agent.build_user_profile()
        
        print(f"Analyzing {len(agent.test_events)} past events...")
        print(f"\nProfile created:")
        print(f"- Interest areas: {profile['interest_areas']}")
        print(f"- Keywords (top 10): {profile['keywords'][:10]}")
        print(f"- Preferred domains (top 5): {list(profile['allowlist_domains'])[:5]}")
        print(f"- Credentials: {profile['credentials']}")
        
        # Plan search strategy
        strategy = agent.plan_search_strategy(profile, query)
        print(f"\nSearch strategy for \"{query}\":")
        for i, q in enumerate(strategy.get('search_queries', [])[:2], 1):
            print(f"- Search {i}: \"{q[:80]}...\"" if len(q) > 80 else f"- Search {i}: \"{q}\"")
        print(f"- Keywords to boost: {strategy['search_keywords'][:5]}")
        
        # Save to CSV
        profile_data = [{
            'interest_area': area,
            'keywords': ', '.join(profile['keywords'][:20]),
            'domains': ', '.join(list(profile['allowlist_domains'])[:10])
        } for area in profile['interest_areas']]
        self.save_csv(profile_data, 'editor_profile.csv', cycle)
        
        # Save strategy
        self.save_json(strategy, 'editor_strategy.json', cycle)
        
        return {
            'profile': {k: list(v) if isinstance(v, set) else v for k, v in profile.items()},
            'strategy': strategy
        }
    
    def analyze_researcher(self, query: str, profile: Dict, cycle: int = 1) -> List[Dict]:
        """Analyze Researcher agent output."""
        print("\nRESEARCHER - MULTI-SEARCH:")
        print("="*60)
        
        agent = ResearcherAgent(use_cache=True)
        
        # Execute search with profile
        candidates = agent.search_events(
            query=query,
            keywords=profile.get('keywords', []),
            domains=profile.get('allowlist_domains', []),
            location="NYC",
            max_results=20
        )
        
        print(f"\nCombined: {len(candidates)} unique URLs")
        
        # Analyze domains
        domains = {}
        for c in candidates:
            url = c.get('url', '')
            domain = url.split('/')[2] if '/' in url and url.startswith('http') else 'unknown'
            domains[domain] = domains.get(domain, 0) + 1
        
        print("Top domains:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {domain}: {count} results")
        
        print("\nTop 5 candidates:")
        for i, c in enumerate(candidates[:5], 1):
            print(f"{i}. {c['url'][:60]}... (score: {c.get('score', 0):.2f})")
        
        # Prepare CSV data
        csv_data = []
        for c in candidates:
            url = c.get('url', '')
            domain = url.split('/')[2] if '/' in url and url.startswith('http') else 'unknown'
            
            # Check if URL pattern suggests specific event
            has_event_pattern = any(pattern in url for pattern in [
                '/e/', '/events/', '-tickets-', '/event/'
            ])
            
            csv_data.append({
                'url': url,
                'domain': domain,
                'title': c.get('title', ''),
                'score': c.get('score', 0),
                'snippet': c.get('snippet', '')[:200],
                'search_depth': c.get('search_depth', 'unknown'),
                'has_event_pattern': 'YES' if has_event_pattern else 'NO',
                'published_date': c.get('published_date', '')
            })
        
        self.save_csv(csv_data, 'researcher_candidates.csv', cycle)
        
        return candidates
    
    def analyze_fact_checker(self, candidates: List[Dict], cycle: int = 1) -> List[Dict]:
        """Analyze Fact-Checker agent output."""
        print("\nFACT-CHECKER - EXTRACTION & DEDUPLICATION:")
        print("="*60)
        
        agent = FactCheckerAgent(use_cache=True)
        
        print(f"Processing {len(candidates)} candidates (extracting from top 20)...")
        
        # Extract events
        extracted = agent.extract_from_candidates(
            candidates,
            max_extractions=min(20, len(candidates)),
            use_llm=True
        )
        
        print(f"\nExtraction results:")
        
        # Analyze extraction quality
        good_events = []
        profile_pages = []
        calendar_pages = []
        past_events = []
        
        for e in extracted:
            title = e.get('title', '').lower()
            if 'not a specific event' in title or not e.get('title'):
                if 'calendar' in title or 'events' in title:
                    calendar_pages.append(e)
                else:
                    profile_pages.append(e)
            elif e.get('is_past_event'):
                past_events.append(e)
            elif e.get('has_basic_info'):
                good_events.append(e)
        
        if good_events:
            for e in good_events[:3]:
                print(f"✓ {e['source_url'][:40]}... → \"{e['title']}\" ({e.get('date')}, {e.get('time')}, {e.get('location')})")
        
        if profile_pages:
            print(f"✗ {len(profile_pages)} profile pages (not events)")
        if calendar_pages:
            print(f"✗ {len(calendar_pages)} calendar/listing pages (not specific events)")
        if past_events:
            print(f"✗ {len(past_events)} past events")
        
        print(f"\nLLM Deduplication:")
        print(f"- Input: {len(candidates)} candidates")
        print(f"- Extracted: {len(extracted)} events")
        print(f"- With basic info: {len(good_events)}/{len(extracted)} ({len(good_events)/len(extracted)*100:.0f}%)" if extracted else "- No events extracted")
        
        # Prepare CSV data
        csv_data = []
        for e in extracted:
            title = e.get('title', '')
            
            # Determine why it's not a good event
            why_not = ""
            if 'not a specific event' in title.lower():
                why_not = "Generic page, not specific event"
            elif 'calendar' in title.lower():
                why_not = "Calendar page, not specific event"
            elif not e.get('date') and not e.get('time'):
                why_not = "Missing date/time"
            elif e.get('is_past_event'):
                why_not = "Past event"
            elif not e.get('has_basic_info'):
                why_not = "Missing basic info"
            else:
                why_not = "OK"
            
            csv_data.append({
                'title': title,
                'url': e.get('source_url', ''),
                'date': e.get('date'),
                'time': e.get('time'),
                'location': e.get('location'),
                'organizer': e.get('organizer'),
                'has_basic_info': e.get('has_basic_info', False),
                'is_past': e.get('is_past_event', False),
                'is_duplicate_of': e.get('is_duplicate_of'),
                'why_not_event': why_not,
                'summary': e.get('summary', '')[:200]
            })
        
        self.save_csv(csv_data, 'factchecker_events.csv', cycle)
        
        return extracted
    
    def analyze_publisher(self, events: List[Dict], profile: Dict, cycle: int = 1) -> Dict:
        """Analyze Publisher agent output."""
        print("\nPUBLISHER - SCORING & GATE DECISION:")
        print("="*60)
        
        if not events:
            print("No events to score")
            return {'top10': [], 'decision': {'action': 'accept', 'notes': 'No events to score'}}
        
        agent = PublisherAgent()
        
        print(f"Scoring {len(events)} events for user profile...")
        
        # Score and rank
        result = agent.score_and_rank(events, profile, cycle_count=cycle-1)
        
        print("\nResults:")
        for i, event in enumerate(result['top10'][:5], 1):
            score = event.get('recommendation', 0)
            symbol = "✓" if score >= 0.3 else "✗"
            print(f"{i}. {symbol} \"{event.get('title', 'Unknown')[:80]}...\"")
            print(f"   Score: {score:.1f}")
            if score < 0.3:
                print(f"   Issue: {event.get('rationale', '')[:80]}")
        
        viable = len([e for e in result['top10'] if e.get('recommendation', 0) >= 0.3])
        print(f"\nViable events (score ≥ 0.3): {viable}/{len(result['top10'])}")
        
        print(f"\nGATE DECISION: {result['decision']['action'].upper()}")
        print(f"Reason: \"{result['decision']['notes']}\"")
        
        if result['decision']['action'] == 'revise':
            print("Next: Cycling back to Editor for revised strategy...")
        
        # Prepare CSV data
        csv_data = []
        for e in result['top10']:
            csv_data.append({
                'title_generated': e.get('title', ''),
                'original_title': e.get('original_title', ''),
                'score': e.get('recommendation', 0),
                'url': e.get('source_url', ''),
                'date': e.get('date'),
                'time': e.get('time'),
                'location': e.get('location'),
                'has_basic_info': e.get('has_basic_info', False),
                'is_past': e.get('is_past_event', False),
                'rationale': e.get('rationale', ''),
                'access_req': e.get('access_req', '')
            })
        
        self.save_csv(csv_data, 'publisher_scores.csv', cycle)
        
        return result
    
    def run_analysis(self, query: str, max_cycles: int = 2):
        """Run complete user flow analysis."""
        print(f"\nUSER FLOW PIPELINE ANALYSIS")
        print(f"Query: \"{query}\"")
        print("="*60)
        
        all_cycles = []
        
        for cycle in range(1, max_cycles + 1):
            if cycle > 1:
                print(f"\n{'='*60}")
                print(f"CYCLE {cycle} - REVISED STRATEGY")
                print(f"{'='*60}")
            
            cycle_data = {}
            
            # 1. Editor
            editor_result = self.analyze_editor(query, cycle)
            cycle_data['editor'] = editor_result
            
            # 2. Researcher
            candidates = self.analyze_researcher(
                query, 
                editor_result['profile'],
                cycle
            )
            cycle_data['candidates'] = candidates
            
            # 3. Fact-Checker
            extracted = self.analyze_fact_checker(candidates, cycle)
            cycle_data['extracted'] = extracted
            
            # 4. Publisher
            publisher_result = self.analyze_publisher(
                extracted,
                editor_result['profile'],
                cycle
            )
            cycle_data['publisher'] = publisher_result
            
            all_cycles.append(cycle_data)
            
            # Check if we should continue
            if publisher_result['decision']['action'] == 'accept':
                break
        
        # Save complete summary
        summary = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'total_cycles': len(all_cycles),
            'cycles': all_cycles
        }
        self.save_json(summary, 'pipeline_summary.json')
        
        # Generate diagnosis
        self.generate_diagnosis(all_cycles)
        
        print(f"\n{'='*60}")
        print(f"Analysis complete. Results saved to: {self.output_dir}")
        print(f"Review the CSV files for detailed inspection of each stage.")
        
    def generate_diagnosis(self, cycles: List[Dict]):
        """Generate automatic diagnosis of where pipeline fails."""
        diagnosis = []
        
        for i, cycle in enumerate(cycles, 1):
            diagnosis.append(f"CYCLE {i} DIAGNOSIS:")
            
            candidates = cycle.get('candidates', [])
            extracted = cycle.get('extracted', [])
            publisher = cycle.get('publisher', {})
            
            # Diagnose Researcher issues
            if len(candidates) < 10:
                diagnosis.append("- RESEARCHER: Not finding enough candidates")
            
            event_urls = sum(1 for c in candidates if any(
                p in c.get('url', '') for p in ['/e/', '/events/', '-tickets-']
            ))
            if event_urls < 5:
                diagnosis.append("- RESEARCHER: URLs don't look like specific events")
            
            # Diagnose Fact-Checker issues
            if extracted:
                real_events = sum(1 for e in extracted 
                                 if 'not a specific event' not in e.get('title', '').lower())
                if real_events < len(extracted) / 2:
                    diagnosis.append("- FACT-CHECKER: Extracting mostly non-events (calendars/profiles)")
                
                with_info = sum(1 for e in extracted if e.get('has_basic_info'))
                if with_info < len(extracted) * 0.3:
                    diagnosis.append("- FACT-CHECKER: Not extracting date/time/location from events")
            else:
                diagnosis.append("- FACT-CHECKER: Failed to extract any events")
            
            # Diagnose Publisher issues
            if publisher.get('top10'):
                viable = sum(1 for e in publisher['top10'] 
                           if e.get('recommendation', 0) >= 0.3)
                if viable == 0:
                    diagnosis.append("- PUBLISHER: Scoring all events as non-viable")
            
            diagnosis.append("")
        
        # Save diagnosis
        diagnosis_file = self.output_dir / 'diagnosis.txt'
        with open(diagnosis_file, 'w') as f:
            f.write('\n'.join(diagnosis))
        
        print(f"\n[Auto-diagnosis saved to: {diagnosis_file}]")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze LocAIted user flow with complete visibility"
    )
    parser.add_argument(
        "query",
        nargs='?',
        default="Find upcoming protests and cultural events in NYC",
        help="Search query to analyze (default: protests and cultural events)"
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=2,
        help="Maximum workflow cycles to run (default: 2)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for results (default: user_flow_analysis_[timestamp])"
    )
    
    args = parser.parse_args()
    
    analyzer = UserFlowAnalyzer(args.output_dir)
    analyzer.run_analysis(args.query, args.max_cycles)

if __name__ == "__main__":
    main()