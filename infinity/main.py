import uvicorn
from infinity_emb import create_server
from infinity_emb.args import EngineArgs

def main():
    # Initialize the Infinity Fastapi app with GPU support
    engine_args = EngineArgs(
        model_name_or_path="BAAI/bge-reranker-base",
        engine="torch",
        device="cuda",
        bettertransformer=False
    )
    app = create_server(engine_args_list=[engine_args])
    
    # Run the server on port 7997
    uvicorn.run(app, host="0.0.0.0", port=7997)

if __name__ == "__main__":
    main()
