#!/usr/bin/env python3

import unittest

import learn2learn as l2l
import torch as th

NUM_INPUTS = 7
INPUT_SIZE = 10
HIDDEN_SIZE = 20
INNER_LR = 0.01
EPSILON = 1e-8


def close(x, y):
    return (x - y).norm(p=2) <= EPSILON


class TestMAMLAlgorithm(unittest.TestCase):

    def setUp(self):
        self.model = th.nn.Sequential(th.nn.Linear(INPUT_SIZE, HIDDEN_SIZE),
                                      th.nn.ReLU(),
                                      th.nn.Linear(HIDDEN_SIZE, HIDDEN_SIZE),
                                      th.nn.Sigmoid(),
                                      th.nn.Linear(HIDDEN_SIZE, HIDDEN_SIZE),
                                      th.nn.Softmax())

        self.model.register_buffer('dummy_buf', th.zeros(1, 2, 3, 4))

    def tearDown(self):
        pass

    def test_clone_module(self):
        for first_order in [False, True]:
            maml = l2l.algorithms.MAML(self.model,
                                       lr=INNER_LR,
                                       first_order=first_order)
            X = th.randn(NUM_INPUTS, INPUT_SIZE)
            ref = self.model(X)
            for clone in [maml.clone(), maml.clone()]:
                out = clone(X)
                self.assertTrue(close(ref, out))

    def test_graph_connection(self):
        maml = l2l.algorithms.MAML(self.model,
                                   lr=INNER_LR,
                                   first_order=False)
        X = th.randn(NUM_INPUTS, INPUT_SIZE)
        ref = maml(X)
        clone = maml.clone()
        out = clone(X)
        out.norm(p=2).backward()
        for p in self.model.parameters():
            self.assertTrue(hasattr(p, 'grad'))
            self.assertTrue(p.grad.norm(p=2).item() > 0.0)

    def test_adaptation(self):
        maml = l2l.algorithms.MAML(self.model,
                                   lr=INNER_LR,
                                   first_order=False)
        X = th.randn(NUM_INPUTS, INPUT_SIZE)
        clone = maml.clone()
        loss = clone(X).norm(p=2)
        clone.adapt(loss)
        new_loss = clone(X).norm(p=2)
        self.assertTrue(loss >= new_loss)
        new_loss.backward()
        for p in self.model.parameters():
            self.assertTrue(hasattr(p, 'grad'))
            self.assertTrue(p.grad.norm(p=2).item() > 0.0)

    def test_allow_unused(self):
        maml = l2l.algorithms.MAML(self.model,
                                   lr=INNER_LR,
                                   first_order=False,
                                   allow_unused=True)
        clone = maml.clone()
        loss = 0.0
        for i, p in enumerate(clone.parameters()):
            if i % 2 == 0:
                loss += p.norm(p=2)
        clone.adapt(loss)
        loss = 0.0
        for i, p in enumerate(clone.parameters()):
            if i % 2 == 0:
                loss += p.norm(p=2)
        loss.backward()
        for p in maml.parameters():
            self.assertTrue(hasattr(p, 'grad'))

    def test_allow_nograd(self):
        self.model[2].weight.requires_grad = False
        maml = l2l.algorithms.MAML(self.model,
                                   lr=INNER_LR,
                                   first_order=False,
                                   allow_unused=False,
                                   allow_nograd=False)
        clone = maml.clone()

        loss = sum([p.norm(p=2) for p in clone.parameters()])
        try:
            # Check that without allow_nograd, adaptation fails
            clone.adapt(loss)
            self.assertTrue(False, 'adaptation successful despite requires_grad=False')  # Check that execution never gets here
        except:
            # Check that with allow_nograd, adaptation succeeds
            clone.adapt(loss, allow_nograd=True)
            loss = sum([p.norm(p=2) for p in clone.parameters()])
            loss.backward()
            self.assertTrue(self.model[2].weight.grad is None)
            for p in self.model.parameters():
                if p.requires_grad:
                    self.assertTrue(p.grad is not None)

        maml = l2l.algorithms.MAML(self.model,
                                   lr=INNER_LR,
                                   first_order=False,
                                   allow_nograd=True)
        clone = maml.clone()
        loss = sum([p.norm(p=2) for p in clone.parameters()])
        # Check that without allow_nograd, adaptation succeeds thanks to init.
        orig_weight = self.model[2].weight.clone().detach()
        clone.adapt(loss)
        self.assertTrue(close(orig_weight, self.model[2].weight))



if __name__ == '__main__':
    unittest.main()
