// Observe the original FreeLicenseManager without changing manager selection.
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text.Json;

class Probe {
    static void Main(string[] args) {
        var assembly = Assembly.LoadFrom(args[0]);
        var type = assembly.GetType("AI.Framework.License.FreeLicenseManager", true)!;
        var manager = type.GetProperty("Current")!.GetValue(null)!;
        var observations = new List<object>();
        foreach (var id in new[] {0, 1, 42, int.MaxValue, -1}) {
            var get = type.GetMethod("GetFeature", new[] {typeof(int), typeof(string), typeof(string)})!;
            var feature = get.Invoke(manager, new object[] {id, "probe", "Probe"})!;
            var values = new Dictionary<string, object?>();
            foreach (var prop in feature.GetType().GetProperties()) {
                if (prop.GetIndexParameters().Length != 0) continue;
                try {
                    var value = prop.GetValue(feature);
                    values[prop.Name] = value == null ? null : value is bool || value is int ? value : value.ToString();
                } catch (Exception ex) { values[prop.Name] = "ERROR: " + (ex.InnerException ?? ex).Message; }
            }
            feature.GetType().GetMethod("Deauthenticate")!.Invoke(feature, null);
            values["IsAuthenticatedAfterDeauthenticate"] = feature.GetType().GetProperty("IsAuthenticated")!.GetValue(feature);
            feature.GetType().GetMethod("Authenticate")!.Invoke(feature, null);
            values["IsAuthenticatedAfterAuthenticate"] = feature.GetType().GetProperty("IsAuthenticated")!.GetValue(feature);
            observations.Add(new {requestedFeatureID = id, values});
        }
        Console.WriteLine(JsonSerializer.Serialize(new {manager = manager.GetType().FullName,
            assemblyMvid = assembly.ManifestModule.ModuleVersionId, observations},
            new JsonSerializerOptions {WriteIndented = true}));
    }
}
