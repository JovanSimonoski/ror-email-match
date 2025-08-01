from ror_email_match.clients.dns_analyzer import DNSAnalyzer
from ror_email_match.clients.ror_client import RORClient
from ror_email_match.clients.crossref_client import CrossrefClient
from ror_email_match.scoring.match_scorer import MatchScorer
from ror_email_match.output.output_formatter import OutputFormatter


"""
      |   
  \  ___  /                           _________
 _  /   \  _    GÉANT                 |  * *  | Co-Funded by
    | ~ |       Trust & Identity      | *   * | the European
     \_/        Incubator             |__*_*__| Union
      =
"""


class OrganizationFinder:
    """
    Main orchestrator class for finding organizations associated with email addresses.

    Coordinates DNS analysis, ROR queries, match scoring, and result formatting to
    provide comprehensive organizational identification based on email domains.
    """

    def __init__(self):
        """
        Initialize the OrganizationFinder with all required client components.

        Creates instances of DNSAnalyzer, RORClient, CrossrefClient, MatchScorer,
        and OutputFormatter for comprehensive organization identification.

        Parameters:
            None

        Returns:
            None
        """
        self.dns_analyzer = DNSAnalyzer()
        self.ror_client = RORClient()
        self.crossref_client = CrossrefClient()
        self.match_scorer = MatchScorer()
        self.output_formatter = OutputFormatter()

    def find_org_associated_with_email(self, email: str, result_display_limit: int = None) -> None:
        """
        Find and display organizations associated with the given email address.

        Performs comprehensive analysis by:
        1. Extracting domain from email and running DNS analysis
        2. Generating and executing ROR queries
        3. Scoring potential matches using domain similarity and DNS verification
        4. Fetching additional Crossref metadata
        5. Formatting and displaying ranked results

        Parameters:
            email (str): The email address to analyze for organizational associations.
            result_display_limit (int, optional): Maximum number of results to display.
                                                 If None or negative, displays all results.

        Returns:
            None: Results are printed to console via OutputFormatter.
        """
        # Extract domain from email for DNS analysis
        email_domain = self.dns_analyzer.get_domain_from_email(email)

        # Get initial DNS results for email domain only
        initial_dns_results = self.dns_analyzer.run_dns_analysis(email_domain)

        # Generate ROR queries
        queries = self.ror_client.generate_ror_queries(email)

        print("\nGenerated ROR Queries:")
        for query in queries:
            print(f"  {query}")

        results = self.ror_client.fetch_ror_data(queries)

        if not results:
            print("\nNo ROR results found")
            self.output_formatter.print_dns_analysis(initial_dns_results, self.dns_analyzer)
            return

        print(f"\nFound {len(results)} potential organization matches")

        # Score and sort results
        scored_results = []
        for result in results:
            dns_results_for_result = initial_dns_results.copy()
            if result.get('links'):
                website_domain = self.dns_analyzer.get_domain_from_url(result['links'][0])
                if website_domain != email_domain:
                    dns_results_for_result = self.dns_analyzer.run_dns_analysis(email_domain, website_domain)

            scored_results.append(
                (result, self.match_scorer.calculate_match_score(email, result, dns_results_for_result),
                 dns_results_for_result))

        scored_results.sort(key=lambda x: x[1]["total"], reverse=True)

        if not result_display_limit or result_display_limit < 0:
            result_display_limit = len(scored_results)

        if result_display_limit < len(scored_results):
            print(f"Limiting the displayed results to {result_display_limit}")

        self.output_formatter.print_organization_results(
            scored_results, result_display_limit, email_domain,
            self.dns_analyzer, self.crossref_client
        )