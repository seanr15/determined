import sys
import pathlib

from determined.experimental import Determined

# Helper function from Kubeflow Blog Post
def get_validation_metric(checkpoint):
    config = checkpoint.experiment_config
    searcher = config['searcher']
    smaller_is_better = bool(searcher['smaller_is_better'])
    metric_name = searcher['metric']

    metrics = checkpoint.validation['metrics']
    metric = metrics['validationMetrics'][metric_name]
    return metric, smaller_is_better


def is_better(c1, c2):
    m1, smaller_is_better = get_validation_metric(c1)
    m2, _ = get_validation_metric(c2)
    if smaller_is_better and m1 < m2:
        return True
    return False


# Create Determined Object
d = Determined(master='latest-master.determined.ai:8080')

# Setup Experiment
context_dir = pathlib.Path.joinpath(pathlib.Path.cwd(), 'mnist_pytorch')
config = {'description': 'mnist_pytorch_const',
          'data': {'url': 'https://s3-us-west-2.amazonaws.com/determined-ai-test-data/pytorch_mnist.tar.gz'},
          'hyperparameters': {'learning_rate': 1.0,
                              'global_batch_size': 64,
                              'n_filters1': 32,
                              'n_filters2': 64,
                              'dropout1': 0.25,
                              'dropout2': 0.5},
          'searcher': {'name': 'single',
                       'metric': 'validation_loss',
                       'max_length': {'batches': 937},
                       'smaller_is_better': True},
          'entrypoint': 'model_def:MNistTrial'}

# Submit Experiment
experiment = d.create_experiment(config, context_dir)
experiment.wait_for_completion()

# Act on Experiment State
if not experiment.success():
    print(f'Experiment {experiment.id} did not complete successfully')
    sys.exit(1)
print(f'Experiment {experiment.id} completed successfully ')

# Decide to put model into model registry (Code is mostly from Kubeflow blog)
model_name = 'dummy_model'
best_checkpoint = experiment.top_checkpoint()

try:
    model = d.get_model(model_name)

except:  # Model not yet in registry
    print(f'Registering new Model: {model_name}')
    model = d.create_model(model_name)

latest_version = model.get_version()

if not latest_version:
    better = True
else:
    better = is_better(latest_version, best_checkpoint)

if better:
    print(f'Registering new version: {model_name}')
    model.register_version(best_checkpoint.uuid)


