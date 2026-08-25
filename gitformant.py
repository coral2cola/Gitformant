#!/usr/bin/env python

import os
import sys
import time

import requests
from dotenv import load_dotenv

# Trust the operating system's certificate store (e.g. a corporate root CA
# injected by an SSL-inspecting proxy) in addition to certifi, so requests keeps
# working on intercepted corporate networks without disabling verification.
# Optional: a missing truststore package or an older Python just falls back to
# certifi, so this must never be fatal.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# Load environment variables from a local .env file (never commit this file)
load_dotenv()

# Github API token, loaded from the GITHUB_API_TOKEN environment variable / .env file
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN", "")
# List of repos discovered during investigation
repos = []

def main(inform_keyword, confirm_keywords=""):
    # Page count specifies the current page of the search results
    PAGE_COUNT = 1
    # Running total of results still to be paged through; initialized before the
    # request so the paging loop below never sees an undefined value if the
    # initial search raises
    results_count = 0

    # Check to make sure a Github token is filled in
    try:
        if GITHUB_API_TOKEN != "":
            results_log = ""
            # Perform an initial search and return up to 100 results
            count, results = github_search(inform_keyword, "100", str(PAGE_COUNT))
            # Remaining results are kept track of in results_count
            results_count = count
            # Place the results into a variable with the total number
            github_results = [count, results]
            # Output the results to the user
            print(output(github_results, PAGE_COUNT - 1))
            results_log += output(github_results, PAGE_COUNT - 1)
            print("====== DISCOVERED REPOS ======")
            print(log_repo_list())
            # Tell the user the total number of returned results
            print("\nFound %s results on Github." % count)
        else:
            # Github API token is missing, return an error
            print("[!] Github API token is missing!")
            print("> Please set GITHUB_API_TOKEN in a .env file (copy .env.example) before continuing.")
            sys.exit(0)
    except Exception as e:
        print(e)

    # Results exceeded the return limit of 100 per page, enter loop to allow
    # user to go to the next page of results
    while True:
        if results_count >= 100:
            next_page_select = input("\nThere are more results to display, go to next page? (y/n) > ")
            if next_page_select == "y" or next_page_select == "Y":
                try:
                    # User has chosen to see next page of results, increment PAGE_COUNT
                    PAGE_COUNT += 1
                    # Make query for next page of 100 results
                    count, results = github_search(inform_keyword, "100", str(PAGE_COUNT))
                    github_results = [count, results]
                    # Output results of search to user
                    print(output(github_results, PAGE_COUNT - 1))
                    results_log += output(github_results, PAGE_COUNT - 1)
                    # Decrement remaining results by 100
                    results_count -= 100
                    print(log_repo_list())
                    print("\nResult count is now at %s" % str(results_count))
                except Exception as e:
                    print(e)
            else:
                # User does not want to see more results, break loop
                break
        else:
            # Break out of the loop
            break

    # Check if user provided confirmation keywords
    if confirm_keywords != "" and results_count != 0:
        try:
            # Ask user if they would like to perform analysis on returned results
            perform_analysis_select = input("\nWould you like to perform a confidentiality level analysis on the repositories found? (y/n) > ")
            if perform_analysis_select == "y" or perform_analysis_select == "Y":
                # Perform an analysis of how confident Gitformant is of repo confidentiality
                analysis_result = informant_analysis(repos, confirm_keywords)
                exit_and_log(results_log, log_repo_list(), analysis_result, inform_keyword, confirm_keywords)
            else:
                exit_and_log(results_log, log_repo_list(), "", inform_keyword, confirm_keywords)
        except Exception as e:
            print(e)
    # Otherwise, just exit and ask for log output
    else:
        exit_and_log(results_log, log_repo_list(), "", inform_keyword)

def exit_and_log(results_log_output, repo_list_results, informant_analysis_results="", inform_keyword="", confirm_keywords=""):
    if len(repo_list_results) != 0:
        log_select = input("\nWould you like to log results before exiting? (y/n) > ")
        if log_select == "y":
            # Allow user to specify log file name
            log_file_name = input("Enter the log file name > ")
            f = open("%s.txt" % log_file_name, "w+")
            # Record the search summary of which keywords were used in the initial query
            f.write("====== SEARCH SUMMARY ======")
            f.write("\nInformant keyword used: %s" % inform_keyword)
            if confirm_keywords != "":
                f.write("\nConfirmation keywords used: %s" % confirm_keywords)
            f.write("\n")
            # Record the results log from Github code search
            f.write("\n====== RESULTS LOG ======")
            f.write(results_log_output)
            # Record the unique repos discovered
            f.write("\n====== DISCOVERED REPOS ======")
            f.write(repo_list_results)
            # If informant analysis was performed, record that as well
            if informant_analysis_results != "":
                f.write("\n\n====== INFORMANT ANALYSIS RESULTS ======")
                f.write(informant_analysis_results)
            print("\nResults have been logged!")
            exit_banner()
            f.close()
            sys.exit(0)
        else:
            exit_banner()
            sys.exit(0)
    else:
        exit_banner()
        sys.exit(0)

def exit_banner():
    print("\n============================================")
    print("Thank you for using Gitformant! Goodbye...")
    print("============================================")

def remove_dupes(seq):
   # Order preserving remove duplicates from list function
   checked = []
   for e in seq:
       if e not in checked:
           checked.append(e)
   return checked

def log_repo_list():
    # Output list of discovered repos to user
    repo_results = ""
    for repo in remove_dupes(repos):
        repo_results += "\n+ https://github.com/%s" % repo
    return repo_results

def output(data, current_page):
    # Check if the current page is greater than one, if so, update index accordingly
    if current_page > 1:
        count = current_page * 100 + 1
    # But, if the current page is one, then at least 100 results
    # have been returned, just add 1
    elif current_page == 1:
        count = 100 + 1
    # Otherwise, we are at the beginning
    else:
        count = 1
    # Display information about the file where the keyword march was found
    # Show the owner and repository
    output_results = ""
    for snip in data[1]:
        output_result = "\n%s.  File: %s" % (str(count).zfill(2), snip['html_url'])
        output_result += "\n     Owner: %s" % snip['repository']['full_name']
        output_result += "\n     Repository: %s" % snip['repository']['html_url']
        output_result += "\n"
        output_results += output_result
        count += 1
    return output_results

def informant_analysis(repo_names, confirm_keywords):
    print("\nStarting analysis, please wait...")
    # For each unique repo, perform an analysis of how confident the assessment is of
    # the confidentiality level
    analysis_results = ""
    for repo_name in remove_dupes(repo_names):
        analysis_result = "\nRepository: https://github.com/%s" % repo_name
        if confirm_keywords != "":
            confirm_total = len(confirm_keywords)
            confirm_success = 0
            # For each keyword in the confirm_keywords list, check if there was a hit
            # in the repository search
            for keyword in confirm_keywords:
                confirm_count = github_confirmation(repo_name, keyword)
                analysis_result += "\nFound %s hit(s) for: %s" % (confirm_count, keyword)
                if confirm_count != 0:
                    # Increment the successful confirm keyword hit counter
                    confirm_success += 1
            # Confidence level is a measure of how many confirmation keywords were hit
            # and how many in total were provided by the user
            confidence_level = (float(confirm_success) / float(confirm_total)) * 100
            # Depending on the percentage of keywords hit vs keywords provided,
            # assign a description for level of confidence from VERY LOW to VERY HIGH.
            # The zero case must be checked before the generic "< 25" branch,
            # otherwise VERY LOW is unreachable
            if confidence_level >= 75:
                analysis_result += "\nConfidence level: VERY HIGH (%s%%)" % confidence_level
            elif confidence_level >= 50:
                analysis_result += "\nConfidence level: HIGH (%s%%)" % confidence_level
            elif confidence_level >= 25:
                analysis_result += "\nConfidence level: MODERATE (%s%%)" % confidence_level
            elif confidence_level == 0:
                analysis_result += "\nConfidence level: VERY LOW (%s%%)" % confidence_level
            else:
                analysis_result += "\nConfidence level: LOW (%s%%)" % confidence_level
        analysis_result += "\n"
        print(analysis_result)
        analysis_results += analysis_result
    return analysis_results

def github_headers():
    # Authenticate via the Authorization header (the old access_token query
    # parameter was removed by Github in 2020) and pin the API version so the
    # token is never placed in the URL
    return {
        "Authorization": "Bearer %s" % GITHUB_API_TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def github_search(query, per_page="100", page_num="1"):
    # Github Search API endpoint for code on Github
    github_endpoint = "https://api.github.com/search/code"
    # Make the request, letting requests handle query string encoding and
    # applying a timeout so a hung connection cannot block indefinitely
    req = requests.get(
        github_endpoint,
        headers=github_headers(),
        params={"q": '"%s"' % query, "per_page": per_page, "page": page_num},
        timeout=15,
    )
    # Save the response in data
    data = req.json()
    # A non-2xx response (bad token, rate limit, invalid query) has no 'items',
    # so bail out cleanly instead of iterating over None
    if not req.ok:
        print("[!] Github API error (%s): %s" % (req.status_code, data.get("message", "unknown error")))
        return 0, []
    # For each repo name, append it to the global repo list
    for result in data.get("items", []):
        # Fetch the repo name and add it to the list of repos seen in results
        repo_name = result["repository"]["full_name"]
        repos.append(repo_name)
    # Return the total number of results and the items
    return data.get("total_count", 0), data.get("items", [])

def github_confirmation(repo, confirms):
    # Github Search API endpoint, limited to a specific repository's code
    github_endpoint = "https://api.github.com/search/code"
    # Retry a bounded number of times when the search rate limit is hit; the old
    # code re-read the same response in a loop and could spin forever
    for _ in range(6):
        try:
            # Sleep to avoid going over the API rate limit
            time.sleep(5)
            # Re-issue the request on each retry
            req = requests.get(
                github_endpoint,
                headers=github_headers(),
                params={"q": '"%s" repo:%s' % (confirms, repo)},
                timeout=15,
            )
            data = req.json()
            # Rate limit exceeded: sleep and retry with a fresh request
            if req.status_code == 403 and req.headers.get("X-RateLimit-Remaining") == "0":
                print("Rate limit is being hit, sleeping for 10 seconds...")
                time.sleep(10)
                continue
            if not req.ok:
                print("[!] Github API error (%s): %s" % (req.status_code, data.get("message", "unknown error")))
                return 0
            # Return total number of successful confirm keyword hits
            return data.get("total_count", 0)
        except requests.RequestException as e:
            # Return a usable count (0) instead of the exception object, which
            # would break the integer maths in the caller
            print("[!] Request failed: %s" % e)
            return 0
    print("[!] Giving up on '%s' after repeated rate limiting." % repo)
    return 0

if __name__ == "__main__":
    try:
        # If user supplied a second argument, then perform a search with confirmation keywords
        if len(sys.argv) == 3:
            keyword = sys.argv[1]
            confirm_words = sys.argv[2].split(",")
            result = main(keyword, confirm_words)
        # Otherwise, just perform a search with informant keyword
        else:
            keyword = sys.argv[1]
            result = main(keyword)
    except Exception as e:
        print(e)
