import unittest

from tomato.lib import schema

class CommonTest(unittest.TestCase):
	Class = schema.Common
	def testRaise(self):
		test = self.Class(null=False)
		self.assertRaises(schema.Error, test.check, None)
		self.assertFalse(test.check(True))
	def testNull(self):
		test = self.Class(null=True)
		self.assertTrue(test.matches(True))
		self.assertTrue(test.matches(None))
		test = self.Class(null=False)
		self.assertTrue(test.matches(True))
		self.assertFalse(test.matches(None))
		self.assertTrue(test.matches(False))
	def testDefaults(self):
		test = self.Class()
		self.assertFalse(test.null)
		self.assertEquals(test.minValue, None)
		self.assertEquals(test.maxValue, None)
		self.assertEquals(test.options, None)
	def testMinValue(self):
		test = self.Class(minValue=0.0)
		self.assertFalse(test.matches(-1.0))
		self.assertTrue(test.matches(0.0))
		self.assertTrue(test.matches(1.0))
		test = self.Class(minValue=None)
		self.assertTrue(test.matches(-1.0))
		self.assertTrue(test.matches(0.0))
		self.assertTrue(test.matches(1.0))
		test = self.Class(minValue=1.0)
		self.assertFalse(test.matches(-1.0))
		self.assertFalse(test.matches(0.0))
		self.assertTrue(test.matches(1.0))
	def testMaxValue(self):
		test = self.Class(maxValue=0.0)
		self.assertTrue(test.matches(-1.0))
		self.assertTrue(test.matches(0.0))
		self.assertFalse(test.matches(1.0))
		test = self.Class(maxValue=None)
		self.assertTrue(test.matches(-1.0))
		self.assertTrue(test.matches(0.0))
		self.assertTrue(test.matches(1.0))
		test = self.Class(maxValue=-1.0)
		self.assertTrue(test.matches(-1.0))
		self.assertFalse(test.matches(0.0))
		self.assertFalse(test.matches(1.0))
	def testDescribe(self):
		test = self.Class(null=True, minValue=0, maxValue=10)
		self.assertEquals(test.describe(), {'null': True, 'min_value': 0, 'max_value': 10})

class AnyTest(unittest.TestCase):
	Class = schema.Any
	def testAny(self):
		test = self.Class(null=False)
		self.assertTrue(test.matches(True))
		self.assertFalse(test.matches(None))
		self.assertTrue(test.matches(1))
		self.assertTrue(test.matches(4.0))
		self.assertTrue(test.matches([]))
		self.assertTrue(test.matches({}))
		self.assertTrue(test.matches("test"))

class ConstantTest(unittest.TestCase):
	Class = schema.Constant
	def testConstant(self):
		test = self.Class(value="test")
		self.assertTrue(test.matches("test"))
		self.assertFalse(test.matches(None))
	def testDescribe(self):
		test = self.Class(value=1)
		self.assertEquals(test.describe(), {'null': False, 'options': [1]})

class NumberTest(unittest.TestCase):
	Class = schema.Number
	def testType(self):
		test = self.Class()
		self.assertTrue(test.matches(1))
		self.assertFalse(test.matches(None))
		self.assertTrue(test.matches(1.0))
		self.assertFalse(test.matches("test"))
	def testDescribe(self):
		test = self.Class()
		self.assertEquals(test.describe(), {'null': False, 'types': ['int', 'float']})

class IntTest(unittest.TestCase):
	Class = schema.Int
	def testType(self):
		test = self.Class()
		self.assertTrue(test.matches(1))
		self.assertFalse(test.matches(None))
		self.assertFalse(test.matches(1.0))
		self.assertFalse(test.matches("test"))
	def testDescribe(self):
		test = self.Class()
		self.assertEquals(test.describe(), {'null': False, 'types': ['int']})

class SequenceTest(unittest.TestCase):
	Class = schema.Sequence
	def testTypes(self):
		test = self.Class()
		self.assertTrue(test.matches("test"))
		self.assertFalse(test.matches(None))
		self.assertFalse(test.matches(1.0))
		self.assertTrue(test.matches([]))
		self.assertTrue(test.matches((1,2)))
		self.assertFalse(test.matches({}))
	def testMinLength(self):
		test = self.Class(minLength=1)
		self.assertTrue(test.matches("test"))
		self.assertFalse(test.matches([]))
		self.assertTrue(test.matches((1,)))
	def testMaxLength(self):
		test = self.Class(maxLength=1)
		self.assertFalse(test.matches("test"))
		self.assertTrue(test.matches([]))
		self.assertTrue(test.matches((1,)))
		test = self.Class(maxLength=0)
		self.assertFalse(test.matches("test"))
		self.assertTrue(test.matches([]))
	def testDescribe(self):
		test = self.Class(null=True, minLength=0, maxLength=10)
		self.assertEquals(test.describe(), {'null': True, 'min_length': 0, 'max_length': 10,
			'types': ['string', 'list', 'tuple']})

class StringTest(unittest.TestCase):
	Class = schema.String
	def testTypes(self):
		test = self.Class()
		self.assertTrue(test.matches("test"))
		self.assertTrue(test.matches(u"test"))
		self.assertTrue(test.matches(b"test"))
		self.assertFalse(test.matches([]))
	def testRegex(self):
		test = self.Class(regex="a+b")
		self.assertTrue(test.matches("ab"))
		self.assertTrue(test.matches(u"aaab"))
		self.assertFalse(test.matches(""))
		self.assertFalse(test.matches("bb"))

class ListTest(unittest.TestCase):
	Class = schema.List
	def testTypes(self):
		test = self.Class()
		self.assertFalse(test.matches("test"))
		self.assertTrue(test.matches([1,2]))
		self.assertTrue(test.matches(()))
	def testItems(self):
		test = self.Class(items=schema.Number())
		self.assertTrue(test.matches([]))
		self.assertTrue(test.matches([1,2]))
		self.assertFalse(test.matches([1,"aaa"]))
		self.assertFalse(test.matches(["aaa", "bbb"]))
	def testDescribe(self):
		test = self.Class(items=schema.Number())
		self.assertEquals(test.describe(), {'null': False, 'items': {'null': False, 'types': ['int', 'float']},
			'types': ['list', 'tuple']})

class StringMap(unittest.TestCase):
	Class = schema.StringMap
	def testTypes(self):
		test = self.Class(additional=True)
		self.assertFalse(test.matches([1,2]))
		self.assertFalse(test.matches(()))
		self.assertTrue(test.matches({}))
	def testKeyTypes(self):
		test = self.Class(additional=True)
		self.assertTrue(test.matches({}))
		self.assertTrue(test.matches({"aaa": 1}))
		self.assertFalse(test.matches({1: "aaa"}))
	def testItems(self):
		test = self.Class(items={"a": schema.Number(), "b": schema.String()})
		self.assertTrue(test.matches({"a": 1}))
		self.assertTrue(test.matches({"b": "test"}))
		self.assertFalse(test.matches({"a": "test"}))
		self.assertFalse(test.matches({"b": 1}))
	def testRequired(self):
		test = self.Class(items={"a": schema.Number(), "b": schema.String(), "c": schema.List()}, required=['a', 'c'])
		self.assertTrue(test.matches({"a": 1, "c": []}))
		self.assertTrue(test.matches({"a": 4, "c": [], "b": "test"}))
		self.assertFalse(test.matches({"a": 1}))
		self.assertFalse(test.matches({"b": "vvv"}))
	def testAdditional(self):
		test = self.Class(items={"a": schema.Number()}, additional=False)
		self.assertTrue(test.matches({"a": 1}))
		self.assertFalse(test.matches({"a": 4, "c": []}))
		self.assertFalse(test.matches({"a": 1, "xx": "ddd"}))
		test = self.Class(items={"a": schema.Number()}, additional=True)
		self.assertTrue(test.matches({"a": 1}))
		self.assertTrue(test.matches({"a": 4, "c": []}))
		self.assertTrue(test.matches({"a": 1, "xx": "ddd"}))
	def testDescribe(self):
		test = self.Class(items={"a": schema.Number(), "b": schema.String(), "c": schema.List()}, required=['a',
			'c'], additional=True)
		self.assertEquals(test.describe(), {
			'null': False,
			'items': {
				'a': {'null': False, 'types': ['int', 'float']},
				'b': {'null': False, 'types': ['string']},
				'c': {'null': False, 'types': ['list', 'tuple']}
			},
			'required': ['a', 'c'],
			'additional': True,
			'types': ['map']
		})


if __name__ == '__main__':
	unittest.main()