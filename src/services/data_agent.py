from uagents import Agent, Context, Model
from dataclasses import dataclass

data_agent = Agent(
    name="data_agent",
    seed="randomseedidk",
    port=8000,
    endpoint="http://127.0.0.1:8000/data_request"
)

@dataclass
class DataRequest(Model):
    msg: str

@dataclass
class DataResponse(Model):
    resp: str

@data_agent.on_message(model=DataRequest, replies=DataResponse)
async def msg_callback(ctx: Context, sender:str, request: DataRequest) -> None:
    ctx.logger.debug(f"received {request} from {sender}")

if __name__ == "__main__":
    data_agent.run()
