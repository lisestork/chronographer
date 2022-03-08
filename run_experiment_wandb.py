"""
Running several experiments using wandb
# weights and biases
"""
import json
import argparse

import wandb
from src.framework import GraphSearchFramework

def update_config(config, args):
    """ Updating config for sweep (inline params) """
    if args['type_ranking'] is not None:
        config['type_ranking'] = args['type_ranking']
    if args['ordering_domain_range'] is not None:
        if "ordering" not in config:
            config["ordering"] = {}
        config["ordering"]["domain_range"] = int(args['ordering_domain_range'])

    if args['filtering_what'] is not None:
        if "filtering" not in config:
            config["filtering"] = {}
        config["filtering"]["what"] = int(args['filtering_what'])
    if args['filtering_where'] is not None:
        if "filtering" not in config:
            config["filtering"] = {}
        config["filtering"]["where"] = int(args['filtering_where'])
    if args['filtering_when'] is not None:
        if "filtering" not in config:
            config["filtering"] = {}
        config["filtering"]["when"] = int(args['filtering_when'])

    return config


def get_exp_name(config):
    """ Get experiment name, depending on parameters """
    domain_range = config.get('ordering').get('domain_range') if \
        config.get('ordering') and \
            config.get('ordering').get('domain_range') \
            else ""
    if config.get('filtering'):
        what = "what" if \
            config.get('filtering').get('what') else ""
        where = "where" if \
            config.get('filtering').get('where') else ""
        when = "when" if \
            config.get('filtering').get('when') else ""
    return f"{config['type_ranking']}_{domain_range}_{what}_{where}_{when}"

def run_one_iteration(i, framework):
    """ Running one iteration of the search framework """
    output = framework.run_one_iteration(iteration=i)
    framework.info = framework.merge_outputs(output=output, iteration=i,
                                              info=framework.info)

    if framework.to_expand:
        framework.expanded[i+1] = framework.to_expand

        framework.subgraph.to_csv(f"{framework.save_folder}/{i}-subgraph.csv")
        events_found = \
            [str(e) for e in framework.subgraph[framework.subgraph.type_df == "ingoing"] \
                .subject.unique()] + \
                [str(e) for e in framework.subgraph[framework.subgraph.type_df == "outgoing"] \
                    .object.unique()]

        framework.update_metrics(iteration=i, found=events_found)
        framework.pending_nodes_ingoing.to_csv(\
            f"{framework.save_folder}/{i}-pending_nodes_ingoing.csv")
        framework.pending_nodes_outgoing.to_csv(\
            f"{framework.save_folder}/{i}-pending_nodes_outgoing.csv")
        json.dump(framework.occurence, open(f"{framework.save_folder}/{i}-occurences.json",
                                        "w", encoding='utf-8'),
                indent=4)
        # self.info.to_csv(f"{i}-info.csv")
        json.dump(framework.expanded, open(\
            f"{framework.save_folder}/expanded.json", "w", encoding='utf-8'),
                indent=4)
        json.dump(framework.metrics_data, open(\
            f"{framework.save_folder}/metrics.json", "w", encoding='utf-8'),
                indent=4)
        json.dump(framework.info, open(\
            f"{framework.save_folder}/info.json", "w", encoding='utf-8'),
                indent=4)

        framework.plotter(info=json.load(open(f"{framework.save_folder}/metrics.json",
                            "r", encoding="utf-8")),
                save_folder=framework.save_folder)


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-j", "--json", required=True,
                    help="Path to json file containing configuration file")
    ap.add_argument("-tr", "--type_ranking", default=None,
                    help="Type of ranking for scoring the paths")
    ap.add_argument('-odr', '--ordering_domain_range', default=None,
                    help="Boolean, domain/range for reordering")
    ap.add_argument('-fwhat', '--filtering_what', default=None,
                    help="Boolean, filtering with what constraints")
    ap.add_argument('-fwhere', '--filtering_where', default=None,
                    help="Boolean, filtering with where constraints")
    ap.add_argument('-fwhen', '--filtering_when', default=None,
                    help="Boolean, filtering with when constraints")
    args_main = vars(ap.parse_args())
    json_path = args_main["json"]

    if not (args_main["ordering_domain_range"] == "0" and \
        args_main["filtering_where"] == "0" and \
            args_main["filtering_when"] == "0"):

        config_loaded = json.load(open(json_path, "r", encoding="utf-8"))
        config_loaded["rdf_type"] = list(config_loaded["rdf_type"].items())
        config_loaded = update_config(config=config_loaded, args=args_main)

        framework_main = GraphSearchFramework(config=config_loaded)
        PROJECT_NAME = "event-graph-search-framework"
        experiment_name = framework_main.save_folder

        with open(
            f"{framework_main.save_folder}/config.json", "w", encoding='utf-8'
        ) as outfile:
            json.dump(framework_main.config, outfile, indent=4)
        framework_main.expanded = {}
        framework_main.metrics_data = {}
        framework_main.info = {}

        for i_main in range(1, framework_main.iterations+1):
            wandb.init(
                project=PROJECT_NAME,
                name=get_exp_name(config=config_loaded))
            run_one_iteration(i=i_main, framework=framework_main)

            if 
            wandb.log(framework_main.metrics_data[i_main])

        wandb.finish()
