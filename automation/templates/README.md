# Templates
Templates are written in the Jinja2 templating language. These templates are populated by topology_converter.py using information learned from the topology file.

To see a list of the variables that would be passed to a template use the "-dd" which is short for "display datastructure" option.

```
python ./topology_converter.py ./examples/2switch.dot -dd
```

Topology converter allows a user to specify additional templates to be populated in addition to the Vagrantfile template. See the [Documentation](../documentation) section on templates for more information.

