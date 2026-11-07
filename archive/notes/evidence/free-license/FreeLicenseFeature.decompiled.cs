using System;
using System.Runtime.CompilerServices;

namespace AI.Framework.License;

[c(1)]
[b(0)]
public class FreeLicenseFeature : ILicenseFeature
{
	[CompilerGenerated]
	private string a = "";

	[CompilerGenerated]
	private string b = "";

	public int ID
	{
		get
		{
			short num = 19978;
			short num2 = num;
			num = 19978;
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
				return 0;
			}
		}
	}

	public bool IsAuthenticated
	{
		get
		{
			short num = 23547;
			short num2 = num;
			num = 23547;
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
				return true;
			}
		}
	}

	public string Name
	{
		[CompilerGenerated]
		get
		{
			short num = 11427;
			short num2 = num;
			num = 11427;
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
				return a;
			}
		}
		[CompilerGenerated]
		private set
		{
			short num = 147;
			short num2 = num;
			num = 147;
			switch (num2 == num)
			{
			}
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
			a = value;
		}
	}

	public string DisplayName
	{
		[CompilerGenerated]
		get
		{
			short num = -4641;
			short num2 = num;
			num = -4641;
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
				return b;
			}
		}
		[CompilerGenerated]
		internal set
		{
			short num = 7736;
			short num2 = num;
			num = 7736;
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
			if (num != 0)
			{
			}
			b = value;
		}
	}

	public bool IsEnabled
	{
		get
		{
			short num = 1;
			if (num != 0)
			{
			}
			num = -30920;
			short num2 = num;
			num = -30920;
			switch (num2 == num)
			{
			default:
				num = 0;
				_ = num;
				num = 0;
				if (num != 0)
				{
				}
				return true;
			}
		}
	}

	public bool IsExpired
	{
		get
		{
			short num = 9836;
			short num2 = num;
			num = 9836;
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
				return false;
			}
		}
	}

	public LicenseType Type
	{
		get
		{
			short num = 12320;
			short num2 = num;
			num = 12320;
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
				return LicenseType.Product;
			}
		}
	}

	public LicenseLimitType LimitType
	{
		get
		{
			short num = 9146;
			short num2 = num;
			num = 9146;
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
				return LicenseLimitType.Perpetual;
			}
		}
	}

	public int MaximumExecutionCount
	{
		get
		{
			short num = -29270;
			short num2 = num;
			num = -29270;
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
				return int.MaxValue;
			}
		}
	}

	public int CurrentExecutionCount
	{
		get
		{
			short num = 8108;
			short num2 = num;
			num = 8108;
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
				return 0;
			}
		}
	}

	public int RemainingExecutionCount
	{
		get
		{
			short num = -21151;
			short num2 = num;
			num = -21151;
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
				return int.MaxValue;
			}
		}
	}

	public DateTime StartDateTime
	{
		get
		{
			short num = 1;
			if (num != 0)
			{
			}
			num = 7868;
			short num2 = num;
			num = 7868;
			switch (num2 == num)
			{
			default:
				num = 0;
				_ = num;
				num = 0;
				if (num != 0)
				{
				}
				return DateTime.MinValue;
			}
		}
	}

	public DateTime ExpirationDateTime
	{
		get
		{
			short num = 2258;
			short num2 = num;
			num = 2258;
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
				return DateTime.MaxValue;
			}
		}
	}

	public TimeSpan TotalTimeSpan
	{
		get
		{
			short num = -31317;
			short num2 = num;
			num = -31317;
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
				return TimeSpan.MaxValue;
			}
		}
	}

	public TimeSpan RemainingTimeSpan
	{
		get
		{
			short num = -15246;
			short num2 = num;
			num = -15246;
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
				return TimeSpan.MaxValue;
			}
		}
	}

	internal FreeLicenseFeature(string A_0 = "")
	{
		Name = A_0;
	}

	public void Authenticate()
	{
		short num = 25314;
		short num2 = num;
		num = 25314;
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

	public void Deauthenticate()
	{
		short num = 31658;
		short num2 = num;
		num = 31658;
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
