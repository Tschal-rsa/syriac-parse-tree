from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel, ConfigDict

empty = '∅'

system_message = '''You are a Semitic language expert. Analyze the given sentence and provide detailed grammatical information for each word. Imporant: always use the response tool to respond to the user. Never add any other text to the response.

Text: """
Please list all the words in the following sentence: ܘܡܫܟܚܝܢܢ
"""
words: ܘܡܫܟܚܝܢܢ

Text: """
Is there any prefixed analytical word (preposition or ܘ) in the word ܘܡܫܟܚܝܢܢ?
"""
prefix: ܘ

Text: """
Is there any suffixed pronoun (possesive, objective, or attached to participles) in the word ܡܫܟܚܝܢܢ?
"""
suffix: ܢܢ

Text: """
What is the complete form of the word ܡܫܟܚܝ?
"""
complete: ܡܫܟܚܝܢ

Text: """
Is there any prefixed morpheme or suffixed morpheme in the word ܡܫܟܚܝܢ?
"""
prefix: ܡ
suffix: ܝܢ

Text: """
What category does the morpheme of the word ܡ belong to? Choose from preformative, passive prefix, verbal stem morpheme, verbal ending, nominal ending, or emphatic marker.
"""
morpheme_type: performative

Text: """
What category does the morpheme of the word ܫܟܚ belong to? Choose from preformative, passive prefix, verbal stem morpheme, verbal ending, nominal ending, or emphatic marker.
"""
morpheme_type: verbal ending

Text: """
What category does the morpheme of the word ܝܢ belong to? Choose from preformative, passive prefix, verbal stem morpheme, verbal ending, nominal ending, or emphatic marker.
"""
morpheme_type: nominal ending

Text: """
What is the complete form of the word ܢܢ?
"""
complete: ܚܢܢ
'''


def get_question_message(sentence: str) -> str:
    return f"Please list all the words in the following sentence: {sentence}"


class ListWordsResponse(BaseModel):
    '''List the words in the sentence'''

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

    words: list[str]
    '''The list of Syriac words'''


class WordResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

    @staticmethod
    def get_question(word: str) -> str:
        raise NotImplementedError

    def get_part(self, word: str, index: int) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class PrefixedAnalyticalWordResponse(WordResponse):
    '''Any prefixed analytical word of the word'''

    prefix: str | None
    '''The prefixed analytical word of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'Is there any prefixed analytical word (preposition or ܘ) in the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        prefix = self.prefix or ''
        match index:
            case 0:
                return prefix
            case 1:
                return word[len(prefix) :]
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Prefix: {self.prefix or empty}'


class SuffixedPronounResponse(WordResponse):
    '''Any suffixed pronoun of the word'''

    suffix: str | None
    '''The suffixed pronoun of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'Is there any suffixed pronoun (possesive, objective, or attached to participles) in the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        suffix = self.suffix or ''
        match index:
            case 0:
                return word[: len(word) - len(suffix)]
            case 1:
                return suffix
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Suffix: {self.suffix or empty}'


class CompleteFormResponse(WordResponse):
    '''Provide the complete form of the word'''

    complete: str
    '''The complete form of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return f'What is the complete form of the word {word}?'

    def get_part(self, word: str, index: int) -> str:
        return self.complete

    def __str__(self) -> str:
        return f'Complete form: {self.complete or empty}'


class PrefixedSuffixedMorphemeResponse(WordResponse):
    '''Any prefixed or suffixed morpheme of the word'''

    prefix: str | None
    '''The prefixed morpheme of the word'''

    suffix: str | None
    '''The suffixed morpheme of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return (
            f'Is there any prefixed morpheme or suffixed morpheme in the word {word}?'
        )

    def get_part(self, word: str, index: int) -> str:
        prefix = self.prefix or ''
        suffix = self.suffix or ''
        match index:
            case 0:
                return prefix
            case 1:
                return word[len(prefix) : len(word) - len(suffix)]
            case 2:
                return suffix
            case _:
                raise ValueError(
                    f'Invalid index for {self.__class__.__name__}: {index}'
                )

    def __str__(self) -> str:
        return f'Prefix: {self.prefix or empty}, Suffix: {self.suffix or empty}'


class MorphemeTypeResponse(WordResponse):
    '''Provide the type of morpheme of the word'''

    morpheme_type: str
    '''The type of morpheme of the word'''

    @staticmethod
    def get_question(word: str) -> str:
        return (
            f'What category does the morpheme of the word {word} belong to? '
            'Choose from preformative, passive prefix, verbal stem morpheme, '
            'verbal ending, nominal ending, or emphatic marker.'
        )

    def get_part(self, word: str, index: int) -> str:
        return self.morpheme_type

    def __str__(self) -> str:
        return f'Morpheme type: {self.morpheme_type or empty}'


@dataclass
class Node:
    response_type: type[WordResponse]
    children: list[Self | None]


response_tree = Node(
    PrefixedAnalyticalWordResponse,
    [
        None,
        Node(
            SuffixedPronounResponse,
            [
                Node(
                    CompleteFormResponse,
                    [
                        Node(
                            PrefixedSuffixedMorphemeResponse,
                            [
                                Node(MorphemeTypeResponse, []),
                                Node(MorphemeTypeResponse, []),
                                Node(MorphemeTypeResponse, []),
                            ],
                        )
                    ],
                ),
                Node(
                    CompleteFormResponse,
                    [],
                ),
            ],
        ),
    ],
)


registered_responses: list[type[BaseModel]] = [
    ListWordsResponse,
    PrefixedAnalyticalWordResponse,
    SuffixedPronounResponse,
    CompleteFormResponse,
    PrefixedSuffixedMorphemeResponse,
    MorphemeTypeResponse,
]
