# pylint: disable-msg=W0612,E1101
import unittest
import nose
import itertools

from numpy import random, nan
from numpy.random import randn
import numpy as np
from numpy.testing import assert_array_equal

import pandas as pan
import pandas.core.common as com
from pandas.core.api import (DataFrame, Index, Series, Panel, notnull, isnull,
                             MultiIndex, DatetimeIndex, Timestamp)
from pandas.util.testing import (assert_almost_equal, assert_series_equal,
                                 assert_frame_equal, assert_panel_equal)
from pandas.util import py3compat

import pandas.util.testing as tm
import pandas.lib as lib

from numpy.testing.decorators import slow

_verbose = True

#-------------------------------------------------------------------------------
# Indexing test cases


def _generate_indices(f, values=False):
    """ generate the indicies
          if values is True , use the axis values
                    is False, use the range
                    """

    axes = f.axes
    if values:
        axes = [ range(len(a)) for a in axes ]

    return itertools.product(*axes)

def _get_value(f, i, values=False):
    """ return the value for the location i """

    # check agains values
    if values:
        return f.values[i]
     
    # this is equiv of f[col][row].....
    #v = f
    #for a in reversed(i):
    #    v = v.__getitem__(a)
    #return v
    return f.ix[i]

def _get_result(obj, method, key, axis):
    """ return the result for this obj with this key and this axis """

    if isinstance(key, dict):
        key = key[axis]

    # in case we actually want 0 index slicing
    try:
        xp  = getattr(obj, method).__getitem__(_axify(obj,key,axis))
    except:
        xp  = getattr(obj, method).__getitem__(key)
        
    return xp

def _axify(obj, key, axis):
    # create a tuple accessor
    if axis is not None:
        axes = [ slice(None) ] * obj.ndim
        axes[axis] = key
        return tuple(axes)
    return k


class TestIndexing(unittest.TestCase):

    _multiprocess_can_split_ = True

    _objs = set(['series','frame','panel'])
    _typs = set(['ints','labels','mixed','ts','floats','empty'])

    def setUp(self):
        import warnings
        warnings.filterwarnings(action='ignore', category=FutureWarning)

        from pandas import date_range

        self.series_ints   = Series(np.random.rand(4), index=range(0,8,2))
        self.frame_ints    = DataFrame(np.random.randn(4, 4), index=range(0, 8, 2), columns=range(0,12,3))
        self.panel_ints    = Panel(np.random.rand(4,4,4), items=range(0,8,2),major_axis=range(0,12,3),minor_axis=range(0,16,4))

        self.series_labels = Series(np.random.randn(4), index=list('abcd'))
        self.frame_labels  = DataFrame(np.random.randn(4, 4), index=list('abcd'), columns=list('ABCD'))
        self.panel_labels  = Panel(np.random.randn(4,4,4), items=list('ZYXW'), major_axis=list('abcd'), minor_axis=list('ABCD'))

        self.series_mixed  = Series(np.random.randn(4), index=[2, 4, 'null', 8])
        self.frame_mixed   = DataFrame(np.random.randn(4, 4), columns=[2, 4, 'null', 8])
        self.panel_mixed   = Panel(np.random.randn(4,4,4), items=[2,4,'null',8])

        self.series_ts     = Series(np.random.randn(4), index=date_range('20130101', periods=4))
        self.frame_ts      = DataFrame(np.random.randn(4, 4), columns=date_range('20130101', periods=4))
        self.panel_ts      = Panel(np.random.randn(4, 4, 4), items=date_range('20130101', periods=4))

        #self.series_floats = Series(np.random.randn(4), index=[1.00, 2.00, 3.00, 4.00])
        #self.frame_floats  = DataFrame(np.random.randn(4, 4), columns=[1.00, 2.00, 3.00, 4.00])
        #self.panel_floats  = Panel(np.random.rand(4,4,4), items = [1.00,2.00,3.00,4.00])

        self.frame_empty   = DataFrame({})
        self.series_empty  = Series({})
        self.panel_empty   = Panel({})

        # form agglomerates
        for o in self._objs:

            d = dict()
            for t in self._typs:
                d[t] = getattr(self,'%s_%s' % (o,t),None)

            setattr(self,o,d)

    def check_values(self, f, func, values = False):
           
        if f is None: return
        axes = f.axes
        indicies = itertools.product(*axes)
        
        for i in indicies:
            result = getattr(f,func)[i]

            # check agains values
            if values:
                expected = f.values[i]
            else:
                expected = f
                for a in reversed(i):
                    expected = expected.__getitem__(a)

            assert_almost_equal(result, expected)


    def check_result(self, name, method1, key1, method2, key2, typs = None, objs = None, axis = None, empty = 'fail', fails = None):


        def _eq(t, o, a, obj, k1, k2):
            """ compare equal for these 2 keys """

            if a is not None and a > obj.ndim-1:
                return

            def _print(result, show = True,error = None):
                if error is not None:
                    error = str(error)
                v = "%-12.12s [%-10.10s]: [typ->%-8.8s,obj->%-8.8s,key1->(%-4.4s) %-20.20s,key2->(%-4.4s) %-20.20s,axis->%s] %s" % (name,result,t,o,method1,key1,method2,key2,a,error or '')
                if show:
                    print(v)

            try:

                rs  = getattr(obj, method1).__getitem__(_axify(obj,k1,a))

                try:
                    xp = _get_result(obj,method2,k2,a)
                except:
                    result = 'no comp'
                    _print(result)
                    return

                try:
                    if np.isscalar(rs) and np.isscalar(xp):
                        self.assert_(rs == xp)
                    elif xp.ndim == 1:
                        assert_series_equal(rs,xp)
                    elif xp.ndim == 2:
                        assert_frame_equal(rs,xp)
                    elif xp.ndim == 3:
                        assert_panel_equal(rs,xp)
                    result = 'ok'
                except (AssertionError):
                    result = 'fail'

                # reverse the checks
                if fails is True:
                    if result == 'fail':
                        result = 'ok (fail)'
                    
                if not result.startswith('ok'):
                    raise AssertionError(_print(result))

                if _verbose:
                    _print(result)

            except (AssertionError):
                raise
            except (TypeError):
                raise AssertionError(_print('type error'))
            except (Exception), detail:

                # if we are in fails, the ok, otherwise raise it
                if isinstance(fails,(tuple,list)):
                    if tuple(t,o) in fails or tuple(o,t) in fails:
                        return
                
                # empty fails are ok
                if empty == 'fail' and t == 'empty':
                    return

                result = 'error'
                raise AssertionError(_print(result, error = detail))

        if typs is None:
            typs = self._typs

        if objs is None:
            objs = self._objs

        axes = []
        if axis is not None:
            if not isinstance(axis,(tuple,list)):
                axes = [ axis ]
            else:
                axes = list(axis)
        else:
            axes = [ 0, 1, 2]

        # check
        for o in objs:
            if o not in self._objs:
                continue

            d = getattr(self,o)
            for a in axes:
                for t in typs:
                    if t not in self._typs:
                        continue

                    obj = d[t]
                    if obj is not None:
                        obj = obj.copy()
                        
                        k2 = key2

                        if name == 'list int' and o == 'panel':
                            import pdb; pdb.set_trace()

                        _eq(t, o, a, obj, key1, k2)

    def test_at_and_iat_get(self):

        def _check(f, func, values = False):
            
            if f is not None:
                indicies = _generate_indices(f, values)
                for i in indicies:
                    result = getattr(f,func)[i]
                    expected = _get_value(f,i,values)
                    assert_almost_equal(result, expected)

        for o in self._objs:
            
            d = getattr(self,o)

            # iat
            _check(d['ints'],'iat', values=True)
            for f in [d['labels'],d['ts'],d['floats']]:
                if f is not None:
                    self.assertRaises(ValueError, self.check_values, f, 'iat')

            # at
            _check(d['ints'],  'at')
            _check(d['labels'],'at')
            _check(d['ts'],    'at')
            _check(d['floats'],'at')
                
    def test_at_and_iat_set(self):

        def _check(f, func, values = False):
            
            if f is not None:
                indicies = _generate_indices(f, values)
                for i in indicies:
                    getattr(f,func)[i] = 1
                    expected = _get_value(f,i,values)
                    assert_almost_equal(expected, 1)

        for t in self._objs:
            
            d = getattr(self,t)

            _check(d['ints'],'iat',values=True)
            for f in [d['labels'],d['ts'],d['floats']]:
                if f is not None:
                    self.assertRaises(ValueError, _check, f, 'iat')

            # at
            _check(d['ints'],  'at')
            _check(d['labels'],'at')
            _check(d['ts'],    'at')
            _check(d['floats'],'at')
            
    def test_iloc_getitem(self):

        # integer
        self.check_result('integer', 'iloc', 2, 'ix', { 0 : 4, 1: 6, 2: 8 }, typs = ['ints'])
        self.check_result('integer', 'iloc', 2, 'ix', { 0 : 4, 1: 6, 2: 8 }, typs = ['labels','mixed','ts','floats','empty'], fails = True)
        
        # neg integer
        self.check_result('neg int', 'iloc', -1, 'ix', { 0 : 6, 1: 9, 2: 12 }, typs = ['ints'])
        self.check_result('neg int', 'iloc', -1, 'ix', { 0 : 6, 1: 9, 2: 12 }, typs = ['labels','mixed','ts','floats','empty'], fails = True)

        # list of ints
        self.check_result('list int', 'iloc', [0,1,3], 'ix', { 0 : [0,2,6], 1 : [0,3,9], 2: [0,4,12] }, typs = ['ints'])
        self.check_result('list int', 'iloc', [0,1,3], 'ix', { 0 : [0,2,6], 1 : [0,3,9], 2: [0,4,12] }, typs = ['labels','mixed','ts','floats','empty'], fails = True)
        self.check_result('list int (dups)', 'iloc', [0,1,1,3], 'ix', { 0 : [0,2,2,6], 1 : [0,3,3,9], 2: [0,4,4,12] }, typs = ['ints'])

        # series like
        s = Series(index=range(1,4))
        self.check_result('array like', 'iloc', s.index, 'ix', [2,4,6], typs = ['ints'])

        # boolean indexers
        b = [True,False,True,False,]
        self.check_result('bool', 'iloc', b, 'ix', b, typs = ['ints'])
        self.check_result('bool', 'iloc', b, 'ix', b, typs = ['labels','mixed','ts','floats','empty'], fails = True)

        # slices
        self.check_result('slice', 'iloc', slice(1,3), 'ix', slice(2,4,2), typs = ['ints'])
        self.check_result('slice', 'iloc', slice(1,3), 'ix', slice(2,4,2), typs = ['labels','mixed','ts','floats','empty'], fails = True)

        # out-of-bounds slice
        self.assertRaises(IndexError, self.frame_ints.iloc.__getitem__, tuple([slice(None),slice(1,5,None)]))
        self.assertRaises(IndexError, self.frame_ints.iloc.__getitem__, tuple([slice(None),slice(-5,3,None)]))
        self.assertRaises(IndexError, self.frame_ints.iloc.__getitem__, tuple([slice(1,5,None)]))
        self.assertRaises(IndexError, self.frame_ints.iloc.__getitem__, tuple([slice(-5,3,None)]))

    def test_iloc_setitem(self):
        df = self.frame_ints

        df.iloc[1,1] = 1
        result = df.iloc[1,1]
        self.assert_(result == 1)

        df.iloc[:,2:3] = 0
        expected = df.iloc[:,2:3]
        result = df.iloc[:,2:3]
        assert_frame_equal(result, expected)

    def test_iloc_multiindex(self):
        df = DataFrame(np.random.randn(3, 3), 
                       columns=[[2,2,4],[6,8,10]],
                       index=[[4,4,8],[8,10,12]])

        rs = df.iloc[2]
        xp = df.irow(2)
        assert_series_equal(rs, xp)

        rs = df.iloc[:,2]
        xp = df.icol(2)
        assert_series_equal(rs, xp)

        rs = df.iloc[2,2]
        xp = df.values[2,2]
        self.assert_(rs == xp)

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'],
                   exit=False)
