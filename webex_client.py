#!/usr/bin/env python3
"""
Simple Webex Logs Natural Language Query Client
Uses access token to execute queries and return actual log results.
"""

from pickle import FALSE
import requests
import json
import sys
import time
from nlq_parser import NLQParser

class WebexLogsClient:
    """Simple client to query Webex logs with natural language."""
    
    def __init__(self, cookies_string=None, access_token=None, host="https://logs.o-int.webex.com"):
        """Initialize with cookies or access token."""
        self.host = host
        self.access_token = access_token
        self.parser = NLQParser(enable_logging=True)
        
        # Parse cookies if provided
        self.cookies = {}
        if cookies_string:
            for cookie in cookies_string.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    self.cookies[name.strip()] = value.strip()
        
        # Headers for requests
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "osd-xsrf": "true"
        }
        
        # Add authorization header if using access token
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"
    
    def query(self, natural_language, verbose=True):
        """Execute natural language query and return results."""
        if verbose:
            print(f"🔍 Query: '{natural_language}'")
        
        # Generate OpenSearch query
        query_json = self.parser.parse(natural_language)
        
        try:
            query_dict = json.loads(query_json)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse query: {query_json}"}
        
        if "error" in query_dict:
            return query_dict
        
        # Log the generated OpenSearch query
        if verbose:
            print(f"🔧 Generated OpenSearch Query:")
            print(json.dumps(query_dict, indent=2))
            print()
        
        # Execute query
        if "api" in query_dict:
            return self._execute_api_query(query_dict["api"], verbose)
        else:
            return self._execute_search_query(query_dict, verbose)
    
    def _execute_api_query(self, api_path, verbose=True):
        """Execute API queries like cluster health."""
        # Try the correct console proxy format first
        console_proxy_url = f"{self.host}/api/console/proxy"
        params = {
            "path": api_path,
            "method": "GET",
            "dataSourceId": ""
        }
        
        if verbose:
            print(f"📍 Trying console proxy: {console_proxy_url}?path={api_path}&method=GET")
        
        try:
            response = requests.get(console_proxy_url, params=params, headers=self.headers, cookies=self.cookies, timeout=10)
            if verbose:
                print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    if verbose:
                        print(f"   📄 Response: {response.text[:200]}...")
                    return {"response": response.text}
            else:
                if verbose:
                    print(f"   ❌ Error: {response.text[:200]}")
        except Exception as e:
            if verbose:
                print(f"   ❌ Exception: {e}")
                
        return {"error": f"API endpoint {api_path} not accessible"}
    
    def _execute_search_query(self, query_dict, verbose=True):
        """Execute search queries using direct OpenSearch index access."""
        # Try both methods: console proxy and direct index access
        
        # Method 1: Direct index search like GET wxm-app:logs*/_search
        console_proxy_url = f"{self.host}/api/console/proxy"
        params = {
            "path": "wxm-app:logs*/_search",
            "method": "POST",
            "dataSourceId": ""
        }
        
        if verbose:
            print(f"🔍 Executing search via console proxy on wxm-app:logs* index...")
        
        try:
            response = requests.post(console_proxy_url, params=params, json=query_dict, 
                                   headers=self.headers, cookies=self.cookies, timeout=15)
            if verbose:
                print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "hits" in data:
                        return self._format_results(data)
                    else:
                        if verbose:
                            print(f"   📄 No hits in response: {json.dumps(data, indent=2)[:200]}...")
                except json.JSONDecodeError:
                    if verbose:
                        print(f"   📄 Non-JSON response: {response.text[:200]}...")
            else:
                if verbose:
                    print(f"   ❌ Error: {response.text[:200]}")
                
        except Exception as e:
            if verbose:
                print(f"   ❌ Exception: {e}")
        
        # Method 2: Fallback to internal API
        return self._try_internal_api(query_dict, verbose)
    
    def _try_internal_api(self, query_dict, verbose=True):
        """Fallback method using internal search API."""
        search_url = f"{self.host}/internal/search/opensearch-with-long-numerals"
        webex_query = self._convert_to_webex_format(query_dict)
        
        search_headers = {**self.headers}
        search_headers.update({
            "osd-version": "2.19.1",
            "osd-xsrf": "osd-fetch",
            "Referer": f"{self.host}/app/data-explorer/discover"
        })
        
        if verbose:
            print(f"🔄 Trying internal API as fallback...")
        
        try:
            response = requests.post(search_url, json=webex_query, headers=search_headers, 
                                   cookies=self.cookies, timeout=15)
            if verbose:
                print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "rawResponse" in data and "hits" in data["rawResponse"]:
                    return self._format_results(data["rawResponse"])
                    
        except Exception as e:
            if verbose:
                print(f"   ❌ Exception: {e}")
        
        return {"error": "Unable to execute search query - all methods failed"}
    
    def _convert_to_webex_format(self, query_dict):
        """Convert our OpenSearch query to Webex internal API format."""
        # Extract components from our query
        size = query_dict.get("size", 50)
        query = query_dict.get("query", {"match_all": {}})
        
        # Convert bool query structure to Webex format
        webex_body = {
            "sort": [{"@timestamp": {"order": "desc", "unmapped_type": "boolean"}}],
            "size": min(size, 5000),  # Webex seems to limit to 5000
            "version": True,
            "stored_fields": ["*"],
            "script_fields": {},
            "_source": {"excludes": []},
            "query": {
                "bool": {
                    "must": [{"match_all": {}}],
                    "filter": [],
                    "should": [],
                    "must_not": []
                }
            }
        }
        
        # Convert our query to filter format
        if "bool" in query and "must" in query["bool"]:
            for condition in query["bool"]["must"]:
                if "term" in condition:
                    # Convert term queries to match_phrase
                    for field, value in condition["term"].items():
                        webex_body["query"]["bool"]["filter"].append({
                            "match_phrase": {field: value}
                        })
                elif "range" in condition:
                    # Keep range queries as-is
                    webex_body["query"]["bool"]["filter"].append(condition)
                elif "match" in condition:
                    # Convert match to match_phrase for consistency
                    for field, value in condition["match"].items():
                        webex_body["query"]["bool"]["filter"].append({
                            "match_phrase": {field: value}
                        })
        
        # Wrap in Webex API format
        return {
            "params": {
                "index": "wxm-app:logs*",
                "body": webex_body
            },
            "preference": int(time.time() * 1000)  # Use current timestamp
        }
    
    def _format_results(self, opensearch_response):
        """Format OpenSearch results for display."""
        hits = opensearch_response.get('hits', {})
        total = hits.get('total', {})
        
        if isinstance(total, dict):
            total_count = total.get('value', 0)
        else:
            total_count = total
        
        results = {
            "success": True,
            "total_hits": total_count,
            "query_time_ms": opensearch_response.get('took', 0),
            "logs": []
        }
        
        # Format log entries
        for hit in hits.get('hits', []):
            source = hit.get('_source', {})
            
            log_entry = {
                "timestamp": source.get('@timestamp'),
                "level": source.get('level') or source.get('log', {}).get('level'),
                "service": self._get_service_name(source),
                "message": source.get('message', ''),
                "host": source.get('host', {}).get('name') if isinstance(source.get('host'), dict) else source.get('host'),
                "index": hit.get('_index')
            }
            
            results["logs"].append(log_entry)
        
        return results
    
    def _get_service_name(self, source):
        """Extract service name from log source."""
        service = source.get('service')
        if isinstance(service, dict):
            return service.get('name')
        elif service:
            return str(service)
        
        # Try other fields
        for field in ['serviceName', 'service_name', 'application', 'app']:
            value = source.get(field)
            if value:
                return str(value)
        
        return None
    
    def interactive(self):
        """Interactive query mode."""
        print("🚀 WEBEX LOGS NATURAL LANGUAGE QUERY")
        print("=" * 50)
        print("💬 Ask questions in plain English to get log data!")
        print("📝 Examples:")
        print('   • "errors in last 5 minutes for Hydra"')
        print('   • "warnings from api-gateway in last hour"')
        print('   • "show cluster health"')
        print()
        print("Type 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                query = input("\n💬 What logs do you want? ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                result = self.query(query)
                
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                elif result.get("success"):
                    self._display_results(result)
                elif "cluster_name" in result:
                    print(f"✅ Cluster: {result['cluster_name']}, Status: {result['status']}")
                else:
                    print(f"📄 Response: {json.dumps(result, indent=2)}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"💥 Error: {str(e)}")
    
    def _display_results(self, result):
        """Display search results."""
        total = result.get('total_hits', 0)
        query_time = result.get('query_time_ms', 0)
        logs = result.get('logs', [])
        
        print(f"\n✅ SUCCESS!")
        print(f"📊 Found {total:,} matching logs")
        print(f"⏱️  Query executed in {query_time}ms")
        
        if logs:
            print(f"\n📄 Showing first {min(len(logs), 10)} results:")
            print("=" * 80)
            
            for i, log in enumerate(logs[:10], 1):
                timestamp = log.get('timestamp', 'N/A')
                level = log.get('level', 'N/A')
                service = log.get('service', 'N/A')
                message = log.get('message', 'N/A')[:100]
                
                print(f"\n[{i}] {timestamp} | {level} | {service}")
                print(f"    {message}...")
                
            if len(logs) > 10:
                print(f"\n... and {len(logs) - 10} more results")
        else:
            print("📭 No matching logs found")


def test_simple_search():
    """Test simple search query directly."""
    COOKIES = """amp_533464=X39Tg2m1-ZEAhgPlTuZlAz...1j4a0prre.1j4a0prsf.2.0.2; amp_43702d=EC-qJlDp062pp0ntFgBDPb...1j4a0ps0s.1j4a0ps0s.0.0.0; UnicaNIODID=undefined; _uetvid=766d75603c4f11f08f361703cbc1c6f7; _gcl_au=1.1.617345784.1756978017; ELOQUA=GUID=C3440FB071BE465A896C5FD10F4856C2; utag_main=v_id:0199140cf00e001bc6c9c39d407a05075005606d00b3b$_sn:1$_se:3$_ss:0$_st:1756979819668$ses_id:1756978016271%3Bexp-session$_pn:1%3Bexp-session$ctm_ss:true%3Bexp-session; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Sep+04+2025+15%3A08%3A03+GMT%2B0530+(India+Standard+Time)&version=202407.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=2dd66704-e9f6-4a4b-81fc-33233597a7f3&interactionCount=1&isAnonUser=1&landingPath=https%3A%2F%2Fdeveloper.webex.com%2Fmeeting%2Fdocs%2Fapi%2Fv1%2Fmeetings%2Fregister-a-meeting-registrant&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1; LMAINGRESSCOOKIE=1757936032.505.15526.286679|93d450e5d6409279ec4e9be49d1be4bb; security_authentication_saml1=Fe26.2**46a121760bf00bf9122eb7a339cae0d3061623c1d25b402b3b17c4b8548aff0b*pVGmuC_8cbH0mGdcW1VadA*zvKw8-2RtxCpNpnZ63Ne0LfkAadDC-DLBAcVpcoKZYJe1D-z14zsBSYdaJh4potEVP_R1ZVL8ienWzmgKLy4EkJ_zUg7d0pHfc_KUeR1UNOhKGP36ULEzaV7xQWIarSdw7aqkJ3IUElE41rmpFVR4ajkA2x5diuE36mEuSe8G5k20D0Z1efTDA1xoFSGZGodlEb8Sbmh_MQVE5kNcjwuCZU5q7l_ljeSWMDToBmR630IO_CoElHGBE3tXxLhN6BFlTWRuo7WLIflCh0KRYrTzvpd0L9mKzEUsFpy89qkWw0Zye_qrDAkW3pDIY1b1NRmdr-Loj3nZgjSWLfilXHyk2x7crLJaiTrYtbTUEMmZKUHvaPaS7a8MaOPZ-JjDaUUr7gThgvO36jrrotv-UzAxbFnEof8Cn08hFBlkRQs_LeU97djPa4FmDV8ivPsZkgRATM-sM6cqnZRgRHBxfCSrIybPM-Yt598avDwIOBA1AjbC8J9Wa-xCHatxV28oyM72WxrWXGSojYADCbgs9dvz6LRct1reCd-zATgnR7ON46LS-WREqntAye4Lxiy-IekDlr1I9RfiLYQp8pGBgSGCXlr2mhpLwjzNMvfJewscGIPpXKA5QPAzRG2M6HkO2lgovq04HjDaSAkj9-cHGpGJ74ZmI4Q7yvIeDh0MzggCNWbmcPPO_cSGgpIYwWptRYT**47e51ddbba172336fab3ab8cbe9403271f158b27f70f285cbd43ab238722bc17*YrDT-C4qMDWbplwrhoEfXdX-XJJKlaYBRBX9Enn_ooM; security_authentication=Fe26.2**88fda337c1369bdee7fb870a37f679cffa5d0edb1d08d6aadb19895efa8fa388*VRod_sUzeD_ZwQi4fmzJTQ*A8U2X6HQKHZHbUrEBW6fDyVHh1QboD5cy4wo9TQLW1BmdE3cy8nK3-xGfWsB59XJvuAXxetWHcdAVC0UTtPvhkQij2-di4SvWBLKt69n766bLqbHJTq7H0wrkth1CYcktDxWSNM_1swFg3c-vGxpxKfjH_I1MhD87zFlgnZ3_FA**4a786a176b73ad5824dda47519eb9f8f39430ca121e6ed03049345eab88b0091*5T23qz_rX7LeUyDXQMTru5lg_3eOwchj2tSRdrOIaVw"""
    
    host = "https://logs.o-int.webex.com"
    
    # Parse cookies
    cookies = {}
    for cookie in COOKIES.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "osd-xsrf": "true"
    }
    
    # Simple match_all query
    query = {"query": {"match_all": {}}}
    
    console_proxy_url = f"{host}/api/console/proxy"
    params = {
        "path": "_search",
        "method": "POST",
        "dataSourceId": ""
    }
    
    print("🔍 Testing simple search: GET _search")
    print(f"URL: {console_proxy_url}")
    print(f"Params: {params}")
    print(f"Query: {json.dumps(query, indent=2)}")
    print()
    
    try:
        response = requests.post(console_proxy_url, params=params, json=query, 
                               headers=headers, cookies=cookies, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ SUCCESS!")
                print(f"Response: {json.dumps(data, indent=2)}")
                if "hits" in data:
                    hits = data.get('hits', {})
                    total = hits.get('total', 0)
                    if isinstance(total, dict):
                        total = total.get('value', 0)
                    print(f"\n📊 Found {total} total hits")
                    
                    for i, hit in enumerate(hits.get('hits', [])[:3], 1):
                        print(f"[{i}] {hit.get('_index')} | {hit.get('_source', {})}")
            except json.JSONDecodeError:
                print(f"📄 Non-JSON response: {response.text}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    """Main function."""
    # Your cookies from browser
    COOKIES = """amp_533464=X39Tg2m1-ZEAhgPlTuZlAz...1j4a0prre.1j4a0prsf.2.0.2; amp_43702d=EC-qJlDp062pp0ntFgBDPb...1j4a0ps0s.1j4a0ps0s.0.0.0; UnicaNIODID=undefined; _uetvid=766d75603c4f11f08f361703cbc1c6f7; _gcl_au=1.1.617345784.1756978017; ELOQUA=GUID=C3440FB071BE465A896C5FD10F4856C2; utag_main=v_id:0199140cf00e001bc6c9c39d407a05075005606d00b3b$_sn:1$_se:3$_ss:0$_st:1756979819668$ses_id:1756978016271%3Bexp-session$_pn:1%3Bexp-session$ctm_ss:true%3Bexp-session; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Sep+04+2025+15%3A08%3A03+GMT%2B0530+(India+Standard+Time)&version=202407.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=2dd66704-e9f6-4a4b-81fc-33233597a7f3&interactionCount=1&isAnonUser=1&landingPath=https%3A%2F%2Fdeveloper.webex.com%2Fmeeting%2Fdocs%2Fapi%2Fv1%2Fmeetings%2Fregister-a-meeting-registrant&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1; LMAINGRESSCOOKIE=1757936032.505.15526.286679|93d450e5d6409279ec4e9be49d1be4bb; security_authentication_saml1=Fe26.2**46a121760bf00bf9122eb7a339cae0d3061623c1d25b402b3b17c4b8548aff0b*pVGmuC_8cbH0mGdcW1VadA*zvKw8-2RtxCpNpnZ63Ne0LfkAadDC-DLBAcVpcoKZYJe1D-z14zsBSYdaJh4potEVP_R1ZVL8ienWzmgKLy4EkJ_zUg7d0pHfc_KUeR1UNOhKGP36ULEzaV7xQWIarSdw7aqkJ3IUElE41rmpFVR4ajkA2x5diuE36mEuSe8G5k20D0Z1efTDA1xoFSGZGodlEb8Sbmh_MQVE5kNcjwuCZU5q7l_ljeSWMDToBmR630IO_CoElHGBE3tXxLhN6BFlTWRuo7WLIflCh0KRYrTzvpd0L9mKzEUsFpy89qkWw0Zye_qrDAkW3pDIY1b1NRmdr-Loj3nZgjSWLfilXHyk2x7crLJaiTrYtbTUEMmZKUHvaPaS7a8MaOPZ-JjDaUUr7gThgvO36jrrotv-UzAxbFnEof8Cn08hFBlkRQs_LeU97djPa4FmDV8ivPsZkgRATM-sM6cqnZRgRHBxfCSrIybPM-Yt598avDwIOBA1AjbC8J9Wa-xCHatxV28oyM72WxrWXGSojYADCbgs9dvz6LRct1reCd-zATgnR7ON46LS-WREqntAye4Lxiy-IekDlr1I9RfiLYQp8pGBgSGCXlr2mhpLwjzNMvfJewscGIPpXKA5QPAzRG2M6HkO2lgovq04HjDaSAkj9-cHGpGJ74ZmI4Q7yvIeDh0MzggCNWbmcPPO_cSGgpIYwWptRYT**47e51ddbba172336fab3ab8cbe9403271f158b27f70f285cbd43ab238722bc17*YrDT-C4qMDWbplwrhoEfXdX-XJJKlaYBRBX9Enn_ooM; security_authentication=Fe26.2**88fda337c1369bdee7fb870a37f679cffa5d0edb1d08d6aadb19895efa8fa388*VRod_sUzeD_ZwQi4fmzJTQ*A8U2X6HQKHZHbUrEBW6fDyVHh1QboD5cy4wo9TQLW1BmdE3cy8nK3-xGfWsB59XJvuAXxetWHcdAVC0UTtPvhkQij2-di4SvWBLKt69n766bLqbHJTq7H0wrkth1CYcktDxWSNM_1swFg3c-vGxpxKfjH_I1MhD87zFlgnZ3_FA**4a786a176b73ad5824dda47519eb9f8f39430ca121e6ed03049345eab88b0091*5T23qz_rX7LeUyDXQMTru5lg_3eOwchj2tSRdrOIaVw"""
    
    # Check if we want to run the simple test
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_simple_search()
        return
        
    client = WebexLogsClient(cookies_string=COOKIES)
    
    if len(sys.argv) > 1:
        # Command line mode with verbose debugging enabled
        query = " ".join(sys.argv[1:])
        result = client.query(query, verbose=True)
        
        # Always show final results summary
        print("\n" + "="*50)
        print("FINAL RESULTS:")
        print("="*50)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        elif result.get("success"):
            print(f"✅ Found {result['total_hits']} results")
            if result.get('logs'):
                print(f"\nShowing first {min(len(result.get('logs', [])), 5)} results:")
                for i, log in enumerate(result.get('logs', [])[:5], 1):
                    timestamp = log.get('timestamp', 'N/A')
                    level = log.get('level', 'N/A') 
                    service = log.get('service', 'N/A')
                    message = log.get('message', 'N/A')[:80]
                    print(f"[{i}] {timestamp} | {level} | {service} | {message}...")
            else:
                print("No logs to display.")
        else:
            print("📄 Raw Response:")
            print(json.dumps(result, indent=2))
    else:
        # Interactive mode
        client.interactive()


if __name__ == "__main__":
    main()
