from smartdashlib import SmartDash
import random
import asyncio

"""use the on_data decorator, which calls the following function after receiving data on the used pin, or simply send data in a while loop
"""
async def main():
    TOKEN = "YOUR_TOKEN"

    smart_dash = SmartDash(token=TOKEN)
    await smart_dash.run()


    @smart_dash.on_data("V100")
    async def random_number(val):
        await smart_dash.write("V1", random.randint(0,10))
    

    @smart_dash.on_data("V3")
    async def toggle_trigger(val):
        if val == 0:
            await smart_dash.switch_trigger("V100", False)
        else:
            await smart_dash.switch_trigger("V100", True)

    

    while True:
        # await smart_dash.write('V2', random.randint(10,20))
        await asyncio.sleep(0.1) #this delay is needed for now


if __name__ == "__main__":
    asyncio.run(main())

