import yaml
import argparse

from easyinstruct import (
    SelfInstructGenerator,
    EvolInstructGenerator,
    BacktranslationGenerator,
    SelfInstructGeneratorWM
)
from easyinstruct import (
    LengthSelector,
    Deduplicator,
    RougeSelector,
    GPTScoreSelector,
    MTLDSelector,
    PPLSelector,
    RandomSelector,
    MultiSelector,
)
from easyinstruct.utils.api import set_openai_key, set_proxy, set_openai_base_url

set_proxy("http://127.0.0.1:7890")


def main(args):
    print("Loading config from {}\n".format(args.config))
    config = yaml.load(open(args.config, "r"), Loader=yaml.FullLoader)
    print(f"Config: {config}\n")
        
    if args.openai_api_key is not None and args.openai_api_key != "":
        set_openai_key(args.openai_api_key)
        
    if args.openai_base_url is not None and args.openai_base_url != "":
        set_openai_base_url(args.openai_base_url)

    if "generator" in config:
        if "SelfInstructGenerator" in config["generator"]:
            generator = SelfInstructGenerator(
                **config["generator"]["SelfInstructGenerator"]
            )
        elif "EvolInstructGenerator" in config["generator"]:
            generator = EvolInstructGenerator(
                **config["generator"]["EvolInstructGenerator"]
            )
        elif "BacktranslationGenerator" in config["generator"]:
            generator = BacktranslationGenerator(
                **config["generator"]["BacktranslationGenerator"]
            )
        # linjh add
        elif "SelfInstructGeneratorWM" in config["generator"]:
            generator = SelfInstructGeneratorWM(
                **config["generator"]["SelfInstructGeneratorWM"]
            )
        else:
            raise NotImplementedError(
                f"Generator {config['generator']} not implemented"
            )

        generator.generate()

    if "selector" in config:
        selectors_list = []
        if "LengthSelector" in config["selector"]:
            selectors_list.append(
                LengthSelector(**config["selector"]["LengthSelector"])
            )
        if "Deduplicator" in config["selector"]:
            selectors_list.append(Deduplicator())
        if "RougeSelector" in config["selector"]:
            selectors_list.append(RougeSelector(**config["selector"]["RougeSelector"]))
        if "GPTScoreSelector" in config["selector"]:
            selectors_list.append(
                GPTScoreSelector(**config["selector"]["GPTScoreSelector"])
            )
        if "MTLDSelector" in config["selector"]:
            selectors_list.append(MTLDSelector(**config["selector"]["MTLDSelector"]))
        if "PPLSelector" in config["selector"]:
            selectors_list.append(PPLSelector(**config["selector"]["PPLSelector"]))
        if "RandomSelector" in config["selector"]:
            selectors_list.append(
                RandomSelector(**config["selector"]["RandomSelector"])
            )

        if len(selectors_list) == 0:
            raise ValueError("No selector specified")
        else:
            selector = MultiSelector(
                source_file_path=config["selector"]["source_file_path"],
                target_dir=config["selector"]["target_dir"],
                target_file_name=config["selector"]["target_file_name"],
                selectors_list=selectors_list,
            )

        selector.process()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    parser.add_argument("--openai_api_key", type=str, default=None)
    parser.add_argument("--openai_base_url", type=str, default=None)
    args = parser.parse_args()
    main(args)
