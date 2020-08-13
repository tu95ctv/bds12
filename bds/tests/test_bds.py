# -*- coding: utf-8 -*-
# from odoo.tests.common import TransactionCase, tagged
from odoo.tests import common
# from odoo.tests import common
print ('tessssssssssssssssttttttt')
from odoo.tests import tagged

@tagged('post_install', 'nice')
class TestBDS(common.TransactionCase):

    # def setUp(self):
    #     print ("*************setup**************")
    #     super(TestBDS, self).setUp()
    def test_abcde(self):
        cr2 = self.registry.cursor()
        self.cr = cr2
        rs = self.env['bds.fetch'].browse(4).fetch()
        cr2.rollback()
        print ('***rs***', rs)
        print ('dau xanh sao khong vao')
        self.assertEqual(
            1,
            1)
        self.cr.rollback()
    def test_some_action(self):
        print  ("*********vào test***********")
        self.assertEquals(
            1,
            0)

