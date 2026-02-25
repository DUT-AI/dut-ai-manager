import zalo_bot
print(dir(zalo_bot))
for item in dir(zalo_bot):
    if not item.startswith('_'):
        obj = getattr(zalo_bot, item)
        print(f"--- {item} ---")
        try:
            print(dir(obj))
        except:
            pass
