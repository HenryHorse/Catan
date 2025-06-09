import unittest

import catan.util as util
import catan.board as board
import catan.player as player
import catan.serialization as serialization

class TestSerialization(unittest.TestCase):
    def test_action_to_neutral_action(self):
        test_board = board.Board(3)

        action_1 = player.EndTurnAction()
        actual_1 = serialization.action_to_neutral_action(action_1)
        expected_1 = serialization.NeutralEndTurnAction()
        self.assertEqual(actual_1, expected_1)
        self.assertEqual(hash(actual_1), hash(expected_1))

        action_2_road_vertex = list(test_board.road_vertices.values())[0]
        action_2 = player.BuildSettlementAction(action_2_road_vertex, False)
        actual_2 = serialization.action_to_neutral_action(action_2)
        expected_2 = serialization.NeutralBuildSettlementAction(action_2_road_vertex.cube_coords)
        self.assertEqual(actual_2, expected_2)
        self.assertEqual(hash(actual_2), hash(expected_2))

        actions_3 = player.TradeAction.simple_trade_options(board.Resource.BRICK, 3)
        actuals_3 = [serialization.action_to_neutral_action(a) for a in actions_3]
        expecteds_3 = [
            serialization.NeutralTradeAction((board.Resource.BRICK, board.Resource.BRICK, board.Resource.BRICK), (board.Resource.WOOD,)),
            serialization.NeutralTradeAction((board.Resource.BRICK, board.Resource.BRICK, board.Resource.BRICK), (board.Resource.GRAIN,)),
            serialization.NeutralTradeAction((board.Resource.BRICK, board.Resource.BRICK, board.Resource.BRICK), (board.Resource.SHEEP,)),
            serialization.NeutralTradeAction((board.Resource.BRICK, board.Resource.BRICK, board.Resource.BRICK), (board.Resource.ORE,)),
        ]
        self.assertEqual(actuals_3, expecteds_3)
        for actual, expected in zip(actuals_3, expecteds_3):
            self.assertEqual(hash(actual), hash(expected))
    
    def test_neutral_action_to_action(self):
        test_board = board.Board(3)
        road_vertex_1 = list(test_board.road_vertices.values())[2]
        road_vertex_2 = list(test_board.road_vertices.values())[5]
        road = board.Road((road_vertex_1, road_vertex_2), 2)

        possible_actions = [
            player.EndTurnAction(),
            player.BuildSettlementAction(road_vertex_1, False),
            player.BuildSettlementAction(road_vertex_2, True),
            player.BuildRoadAction(road, False),
        ]

        neutral_action_1 = serialization.NeutralEndTurnAction()
        actual_1 = serialization.neutral_action_to_action(neutral_action_1, possible_actions)
        expected_1 = player.EndTurnAction()
        self.assertEqual(actual_1, expected_1)
        
        neutral_action_2 = serialization.NeutralBuildSettlementAction(road_vertex_1.cube_coords)
        actual_2 = serialization.neutral_action_to_action(neutral_action_2, possible_actions)
        expected_2 = player.BuildSettlementAction(road_vertex_1, False)
        self.assertEqual(actual_2, expected_2)
        self.assertEqual(actual_2.road_vertex, expected_2.road_vertex)
        self.assertEqual(actual_2.pay_for, False)

        neutral_action_3 = serialization.NeutralBuildSettlementAction(road_vertex_2.cube_coords)
        actual_3 = serialization.neutral_action_to_action(neutral_action_3, possible_actions)
        expected_3 = player.BuildSettlementAction(road_vertex_2, True)
        self.assertEqual(actual_3, expected_3)
        self.assertEqual(actual_3.road_vertex, expected_3.road_vertex)
        self.assertEqual(actual_3.pay_for, True)

        neutral_action_4 = serialization.NeutralBuildRoadAction((road.endpoints[0].cube_coords, road.endpoints[1].cube_coords))
        actual_4 = serialization.neutral_action_to_action(neutral_action_4, possible_actions)
        expected_4 = player.BuildRoadAction(road, False)
        self.assertEqual(actual_4, expected_4)
        self.assertEqual(actual_4.road, expected_4.road)
        self.assertEqual(actual_4.pay_for, False)


if __name__ == '__main__':
    unittest.main()
