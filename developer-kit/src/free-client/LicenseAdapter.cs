// Free client adapter for the A.I.VOICE2 2.14.1 ailm.exe protocol.
// Uses the stock FreeLicenseManager; native engine/voice authentication remains.
using System;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.Json;
using AI.Framework.License;

[assembly: AssemblyVersion("1.0.7.0")]
[assembly: AssemblyFileVersion("1.0.7.0")]
[assembly: AssemblyInformationalVersion("1.0.7-free-client.3")]

internal static class FreeClientLicenseAdapter
{
    private static int Main(string[] args)
    {
        try
        {
            // Opt-in local diagnostics for protocol compatibility investigations.
            string trace = Environment.GetEnvironmentVariable("AIVOICE2_ADAPTER_TRACE");
            if (!string.IsNullOrEmpty(trace))
            {
                // Validation IDs/product labels are useful for diagnostics. Never
                // retain user-entered keys passed to activation management commands.
                var traceArgs = args.Length > 0 && (args[0] == "validate" || args[0] == "--free-client-info")
                    ? args : new[] { args.Length > 0 ? args[0] : "", "[arguments omitted]" };
                System.IO.File.AppendAllText(trace, JsonSerializer.Serialize(traceArgs) + Environment.NewLine);
            }
            LicenseManager.Current = FreeLicenseManager.Current;
            if (args.Length == 1 && (args[0] == "--version" || args[0] == "-v"))
            {
                Console.WriteLine("1.0.7.0");
                return 0;
            }
            if (args.Length == 2 && args[0] == "--free-client-info")
            {
                // Diagnostic explicitly requested by a developer, never needed by the GUI.
                var feature = LicenseManager.Current.GetFeature(int.Parse(args[1]), "AIVOICE2");
                Console.WriteLine(JsonSerializer.Serialize(new {
                    manager = LicenseManager.Current.GetType().FullName,
                    feature.IsEnabled, feature.IsAuthenticated, feature.IsExpired,
                    type = feature.Type.ToString(), limit = feature.LimitType.ToString()
                }));
                return 0;
            }
            string product = "AIVOICE2";
            if (args.Length >= 4 && args[args.Length - 2] == "--product")
                product = args[args.Length - 1];
            if ((args.Length == 2 || args.Length == 4) && args[0] == "validate")
            {
                var feature = LicenseManager.Current.GetFeature(int.Parse(args[1]), product);
                feature.Authenticate();
                if (!feature.IsEnabled || !feature.IsAuthenticated || feature.IsExpired)
                    throw new InvalidOperationException("Free feature is unavailable");
                var header = JsonSerializer.Serialize(new { alg = "HS256", typ = "JWT" });
                var claim = JsonSerializer.Serialize(new {
                    iat = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture),
                    product = feature.Name,
                    // The stock License Confirmation page hides entries with an
                    // empty activation_key and displays nonempty values as captions.
                    // This is a free-client caption, not a personal activation key.
                    activation_key = "Full version",
                    trial_version = feature.Type == LicenseType.Trial,
                    license_type = "perpetual",
                    expired_date = feature.ExpirationDateTime.ToUniversalTime().ToString("o", CultureInfo.InvariantCulture),
                    usable_period = "0",
                    start_date = feature.StartDateTime.ToUniversalTime().ToString("o", CultureInfo.InvariantCulture)
                });
                string payload = Convert.ToBase64String(Encoding.UTF8.GetBytes(header)) + "." +
                                 Convert.ToBase64String(Encoding.UTF8.GetBytes(claim));
                // Preserve the stock local GUI message codec. No embedded key, personal
                // activation, Pretender singleton, fingerprint or network access is used.
                var sign = typeof(PretenderLicenseManager).GetMethods(BindingFlags.Static | BindingFlags.NonPublic)
                    .Single(m => !m.IsGenericMethod && m.ReturnType == typeof(string)
                        && m.GetParameters().Length == 1 && m.GetParameters()[0].ParameterType == typeof(string));
                Console.WriteLine(payload + "." + (string)sign.Invoke(null, new object[] {payload}));
                return 0;
            }
            if (args.Length == 1 && args[0] == "id")
            {
                Console.WriteLine(LicenseManager.Current.GetFingerPrint());
                return 0;
            }
            // Activation management is unnecessary for this free client. Keep harmless
            // stock command shapes so menu actions cannot start the trial/WMI flow.
            if (args.Length >= 2 && (args[0] == "trial" || args[0] == "activate" ||
                                     args[0] == "deactivate" || args[0] == "offline"))
                return 0;
            throw new ArgumentException("Invalid argument.");
        }
        catch (Exception exception)
        {
            Console.WriteLine("0xffff\n    " + (exception.InnerException ?? exception).Message);
            return 1;
        }
    }
}
