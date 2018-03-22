# -*- coding: utf-8 -*-
from copy import deepcopy
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Code
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.utils import CalculationFactory
from aiida.work.workchain import while_
from aiida_quantumespresso.common.workchain.base.restart import BaseRestartWorkChain
from aiida_quantumespresso.data.forceconstants import ForceconstantsData
from aiida_quantumespresso.utils.resources import get_default_options


Q2rCalculation = CalculationFactory('quantumespresso.q2r')


class Q2rBaseWorkChain(BaseRestartWorkChain):
    """
    Base Workchain to launch a Quantum Espresso q2r.x calculation and restart it until
    successfully finished or until the maximum number of restarts is exceeded
    """
    _verbose = True
    _calculation_class = Q2rCalculation

    @classmethod
    def define(cls, spec):
        super(Q2rBaseWorkChain, cls).define(spec)
        spec.input('code', valid_type=Code)
        spec.input('parent_folder', valid_type=FolderData)
        spec.input('parameters', valid_type=ParameterData, required=False)
        spec.input('settings', valid_type=ParameterData, required=False)
        spec.input('options', valid_type=ParameterData, required=False)
        spec.outline(
            cls.setup,
            cls.validate_inputs,
            while_(cls.should_run_calculation)(
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.results,
        )
        spec.output('force_constants', valid_type=ForceconstantsData)
        spec.output('remote_folder', valid_type=RemoteData)

    def validate_inputs(self):
        """
        Define context dictionary 'inputs_raw' with the inputs for the Q2rCalculations as they were at the beginning
        of the workchain. Changes have to be made to a deep copy so this remains unchanged and we can always reset
        the inputs to their initial state. Inputs that are not required by the workchain will be given a default value
        if not specified or be validated otherwise.
        """
        self.ctx.inputs_raw = AttributeDict({
            'code': self.inputs.code,
            'parent_folder': self.inputs.parent_folder,
        })

        if 'parameters' in self.inputs:
            self.ctx.inputs_raw.parameters = self.inputs.parameters.get_dict()
        else:
            self.ctx.inputs_raw.parameters = {'INPUT': {}}

        if 'settings' in self.inputs:
            self.ctx.inputs_raw.settings = self.inputs.settings.get_dict()
        else:
            self.ctx.inputs_raw.settings = {}

        if 'options' in self.inputs:
            self.ctx.inputs_raw.options = self.inputs.options.get_dict()
        else:
            self.ctx.inputs_raw.options = get_default_options()

        # Assign a deepcopy to self.ctx.inputs which will be used by the BaseRestartWorkChain
        self.ctx.inputs = deepcopy(self.ctx.inputs_raw)