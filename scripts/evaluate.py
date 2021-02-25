from argparse import ArgumentParser

from allennlp.commands.train import train_model
from allennlp.common import Params
from allennlp.common.util import import_module_and_submodules

from allennlp.data import DataLoader, DatasetReader, Instance, Vocabulary
from allennlp.models.model import Model
from allennlp.training.trainer import Trainer

from allennlp.nn import util as nn_util
from allennlp.training import util as training_util
from allennlp.common import util as common_util
from allennlp.training.metric_tracker import MetricTracker


import glob
import sys
import os

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("ERROR")

def main():
    parser = ArgumentParser()
    parser.add_argument('--test', nargs='+', action='store')
    parser.add_argument('--config', action='store')
    parser.add_argument('--model', action='store', default='bert')
    parser.add_argument('--path', action='store', default='models/ud.all_pud.none.20.underparam')
    args = parser.parse_args()

    import_module_and_submodules("model")
    import_module_and_submodules("loader")

    model_name = 'xlm-roberta-large' if args.model == 'xlmr' else 'bert-base-multilingual-cased'
    config = Params.from_file(args.config, ext_vars={'train_path': "", 'val_path': "", 'model_size': "", 'lca': "",
                                                     'freeze': "", 'model_name': model_name})
    cuda_device = config.get('trainer').get('cuda_device')

    reader = DatasetReader.from_params(config.get('dataset_reader'))
    model = Model.load(config.duplicate(), args.path, os.path.join(args.path, 'model_state_epoch_19.th'), cuda_device=cuda_device)
    old_vocab = model.vocab

    print(args.test)
    for i in args.test:
        model.vocab = old_vocab
        lang = i.split("/")[-1].split("_")[0]
        test_data = reader.read(i)
        model.vocab.extend_from_instances(test_data)
        model.extend_embedder_vocab()
        test_data.index_with(model.vocab)

        loader = DataLoader(test_data)

        results = training_util.evaluate(model, loader, cuda_device=cuda_device, batch_weight_key=None)
        sys.stdout.write("! {}\t{:.2f}\t{:.2f}\n".format(lang, 100 * results['UAS'], 100 * results['LAS']))

main()