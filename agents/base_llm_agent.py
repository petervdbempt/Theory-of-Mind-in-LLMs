from game.colored_trails import Game_ct
from agents.utils import format_chips, parse_response, construct_prompt


class BaseLLMAgent:
    def __init__(self, player_id):
        self.player_id = player_id
        self.game = None
        self.history = []
        self.order = "LLM"
        self.confidence = 1.0

    def init(self, game):
        self.game = game
        self.history = []

    def make_offer(self, offer_received=None):
        if self.game is None:
            raise ValueError("Agent not initialized with a game instance.")

        if offer_received is not None:
            opp_offer_str = format_chips(Game_ct.convert_code(offer_received, self.game.bin_max))
            prefix = "Rejected your offer and Counter-Proposed" if any(
                h.startswith("You:") for h in self.history) else "Proposes"
            self.history.append(f"Opponent: {prefix} {opp_offer_str}")

        prompt = construct_prompt(self.player_id, self.game, self.history, offer_received)

        # This calls the method defined in the child classes (API or HF)
        response_text = self._generate_llm_response(prompt)

        print(f"  [Debug] Prompt: {prompt}")
        print(f"  [Debug] Raw Response: {response_text}")

        response_data = parse_response(response_text)

        if response_data is None:
            raise ValueError(f"P{self.player_id}: Failed to parse LLM response.")
        action = response_data.get('action', 'withdraw').lower()

        print(f"  [Debug] Parsed Response: Action: {action}, Reason: {response_data.get('reasoning', 'N/A')}")

        if action == 'accept':
            if offer_received is None:
                raise ValueError(f"P{self.player_id}: Tried to accept on the opening turn.")
            return offer_received

        if action == 'propose':
            my_offer_list = response_data.get('offer', [])
            if len(my_offer_list) == 5 and all(0 <= my_offer_list[i] <= self.game.bin_max[i] for i in range(5)):
                self.history.append(f"You: Propose {format_chips(my_offer_list)}")
                return Game_ct.convert_chips(my_offer_list, self.game.bin_max)
            raise ValueError(f"P{self.player_id}: Invalid proposal format/bounds: {my_offer_list}.")

        if action == 'withdraw':
            return self.game.chip_sets[self.player_id]

        raise ValueError(f"P{self.player_id}: Unknown action '{action}'.")

    def _generate_llm_response(self, prompt):
        """Must be implemented by child classes."""
        raise NotImplementedError("This method should be overridden by subclass")