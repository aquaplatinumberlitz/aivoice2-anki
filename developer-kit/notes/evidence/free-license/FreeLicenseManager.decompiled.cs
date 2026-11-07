using System;

namespace AI.Framework.License;

[c(1)]
[b(0)]
public class FreeLicenseManager : ILicenseManager
{
	[b(2)]
	private static FreeLicenseManager a;

	public static FreeLicenseManager Current
	{
		get
		{
			short num = -27939;
			short num2 = num;
			num = -27939;
			int num3;
			switch (num2 == num)
			{
			default:
				num = 0;
				if (num != 0)
				{
				}
				num = 1;
				num3 = num;
				goto IL_0067;
			case false:
			case true:
				{
					a = new FreeLicenseManager();
					num = 0;
					_ = num;
					num = 0;
					num3 = num;
					goto IL_0067;
				}
				IL_0067:
				while (true)
				{
					switch (num3)
					{
					case 1:
						switch (0)
						{
						default:
							continue;
						case 0:
							break;
						}
						goto default;
					default:
						num = 1;
						if (num != 0)
						{
						}
						if (a == null)
						{
							num = 2;
							num3 = num;
							continue;
						}
						goto case 0;
					case 2:
						break;
					case 0:
						return a;
					}
					break;
				}
				goto case false;
			}
		}
	}

	public Uri DefaultHostUri
	{
		get
		{
			short num = -20000;
			short num2 = num;
			num = -20000;
			switch (num2 == num)
			{
			default:
				num = 1;
				if (num != 0)
				{
				}
				num = 0;
				_ = num;
				num = 0;
				if (num != 0)
				{
				}
				return new Uri("");
			}
		}
	}

	public ILicenseFeature GetFeature(int featureID)
	{
		short num = 22722;
		short num2 = num;
		num = 22722;
		switch (num2 == num)
		{
		default:
			num = 1;
			if (num != 0)
			{
			}
			num = 0;
			_ = num;
			num = 0;
			if (num != 0)
			{
			}
			return new FreeLicenseFeature();
		}
	}

	public ILicenseFeature GetFeature(int featureID, string featureName)
	{
		short num = -26950;
		short num2 = num;
		num = -26950;
		switch (num2 == num)
		{
		default:
			num = 1;
			if (num != 0)
			{
			}
			num = 0;
			_ = num;
			num = 0;
			if (num != 0)
			{
			}
			return new FreeLicenseFeature(featureName);
		}
	}

	public ILicenseFeature GetFeature(int featureID, string featureName, string displayName)
	{
		short num = -9173;
		short num2 = num;
		num = -9173;
		switch (num2 == num)
		{
		default:
			num = 1;
			if (num != 0)
			{
			}
			num = 0;
			_ = num;
			num = 0;
			if (num != 0)
			{
			}
			return new FreeLicenseFeature(featureName);
		}
	}

	public void Activate(string activationKey, Uri hostUri, string productName = "")
	{
		short num = -24527;
		short num2 = num;
		num = -24527;
		switch (num2 == num)
		{
		}
		num = 1;
		if (num != 0)
		{
		}
		num = 0;
		_ = num;
		num = 0;
		if (num == 0)
		{
		}
	}

	public string GetFingerPrint()
	{
		short num = 267;
		short num2 = num;
		num = 267;
		switch (num2 == num)
		{
		default:
			num = 0;
			if (num != 0)
			{
			}
			num = 0;
			_ = num;
			num = 1;
			if (num != 0)
			{
			}
			return "";
		}
	}

	public string GetLicense(string activationKey, string c2v, Uri hostUri)
	{
		short num = -15070;
		short num2 = num;
		num = -15070;
		switch (num2 == num)
		{
		default:
			num = 0;
			if (num != 0)
			{
			}
			num = 0;
			_ = num;
			num = 1;
			if (num != 0)
			{
			}
			return "";
		}
	}

	public void Attach(string v2c, string productName = "")
	{
		short num = -17795;
		short num2 = num;
		num = -17795;
		switch (num2 == num)
		{
		}
		num = 1;
		if (num != 0)
		{
		}
		num = 0;
		_ = num;
		num = 0;
		if (num == 0)
		{
		}
	}
}
You are not using the latest version of the tool, please update.
Latest version is '11.2.0.10050' (yours is '9.1.0.7988')
