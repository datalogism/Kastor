"""
Script to load all Kastor models from HuggingFace and test them with sample abstracts.
Models: https://huggingface.co/Datartisan/models

Each model is specialized for a different entity type (Scientist, Politician, Artist, etc.)
"""

import json
import torch
from transformers import AutoTokenizer, BartForConditionalGeneration
from huggingface_hub import hf_hub_download
from datetime import datetime

# Configuration
CHECKPOINT_NAMES = ["last.ckpt","model.ckpt"]

# All Kastor models with sample Wikipedia abstracts and entity IDs
KASTOR_MODELS = {
    "KastorAirport": {
        "repo": "Datartisan/KastorAirport",
        "id_ent": "Los_Angeles_International_Airport",
        "abstract": "Los Angeles International Airport (IATA: LAX, ICAO: KLAX, FAA LID: LAX), commonly referred to as LAX, is the primary international airport serving Los Angeles, California, and its surrounding metropolitan area. LAX is located in the Westchester neighborhood of Los Angeles, 18 miles southwest of Downtown Los Angeles. It is owned and operated by Los Angeles World Airports (LAWA), an agency of the Los Angeles city government."
    },
    "KastorArtist": {
        "repo": "Datartisan/KastorArtist",
        "id_ent": "Pablo_Picasso",
        "abstract": "Pablo Ruiz Picasso was a Spanish painter, sculptor, printmaker, ceramicist and theatre designer who spent most of his adult life in France. He is regarded as one of the most influential artists of the 20th century and is known for co-founding the Cubist movement. He was born on 25 October 1881 in Malaga, Spain and died on 8 April 1973 in Mougins, France."
    },
    "KastorAthlete": {
        "repo": "Datartisan/KastorAthlete",
        "id_ent": "Usain_Bolt",
        "abstract": "Usain St. Leo Bolt is a Jamaican retired sprinter, widely considered to be the greatest sprinter of all time. He is the world record holder in the 100 metres, 200 metres and 4x100 metres relay. He was born on 21 August 1986 in Sherwood Content, Jamaica. Bolt won eight Olympic gold medals across three consecutive Olympic Games."
    },
    "KastorBuilding": {
        "repo": "Datartisan/KastorBuilding",
        "id_ent": "Empire_State_Building",
        "abstract": "The Empire State Building is a 102-story Art Deco skyscraper in Midtown Manhattan, New York City. The building was designed by Shreve, Lamb & Harmon and built from 1930 to 1931. Its name is derived from 'Empire State', the nickname of the state of New York. The building has a roof height of 1,250 feet and stands a total of 1,454 feet tall."
    },
    "KastorCelestialBody": {
        "repo": "Datartisan/KastorCelestialBody",
        "id_ent": "Mars",
        "abstract": "Mars is the fourth planet from the Sun and the second-smallest planet in the Solar System, larger only than Mercury. Mars is a terrestrial planet with a thin atmosphere and has a reddish appearance due to iron oxide on its surface. Mars has two small moons, Phobos and Deimos, which are thought to be captured asteroids."
    },
    "KastorCity": {
        "repo": "Datartisan/KastorCity",
        "id_ent": "Paris",
        "abstract": "Paris is the capital and largest city of France. With an estimated population of 2,102,650 residents in 2023, Paris is the fourth-largest city in the European Union. The city is located on the Seine River in northern France. Paris is known for its museums and architectural landmarks including the Eiffel Tower and the Louvre Museum."
    },
    "KastorCompany": {
        "repo": "Datartisan/KastorCompany",
        "id_ent": "Apple_Inc.",
        "abstract": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California. Apple was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company designs, develops, and sells consumer electronics, computer software, and online services. Apple is the world's largest technology company by revenue."
    },
    "KastorFilm": {
        "repo": "Datartisan/KastorFilm",
        "id_ent": "The_Godfather",
        "abstract": "The Godfather is a 1972 American epic crime film directed by Francis Ford Coppola, who co-wrote the screenplay with Mario Puzo. The film stars Marlon Brando and Al Pacino as the leaders of a fictional New York crime family. The film was released on March 15, 1972. It won three Academy Awards including Best Picture."
    },
    "KastorFood": {
        "repo": "Datartisan/KastorFood",
        "id_ent": "Pizza",
        "abstract": "Pizza is a dish of Italian origin consisting of a usually round, flat base of leavened wheat-based dough topped with tomatoes, cheese, and often various other ingredients, which is then baked at a high temperature. Pizza was first invented in Naples, Italy. The modern pizza was invented by baker Raffaele Esposito in Naples in 1889."
    },
    "KastorMeanOfTransportation": {
        "repo": "Datartisan/KastorMeanOfTransportation",
        "id_ent": "Boeing_747",
        "abstract": "The Boeing 747 is a large, long-range wide-body airliner designed and manufactured by Boeing Commercial Airplanes in the United States. The first flight of the 747 took place on February 9, 1969, and it entered service on January 22, 1970 with Pan Am. The 747 was the first airplane dubbed a 'Jumbo Jet' and has a distinctive hump on its upper deck."
    },
    "KastorMusicalWork": {
        "repo": "Datartisan/KastorMusicalWork",
        "id_ent": "Bohemian_Rhapsody",
        "abstract": "Bohemian Rhapsody is a song by the British rock band Queen. It was written by Freddie Mercury for the band's 1975 album A Night at the Opera. The song is a six-minute suite consisting of several sections without a chorus. It was released as a single on 31 October 1975 and reached number one in the UK Singles Chart."
    },
    "KastorPolitician": {
        "repo": "Datartisan/KastorPolitician",
        "id_ent": "Barack_Obama",
        "abstract": "Barack Hussein Obama II is an American politician and attorney who served as the 44th president of the United States from 2009 to 2017. A member of the Democratic Party, Obama was the first African-American president of the United States. He was born on August 4, 1961, in Honolulu, Hawaii. Before his presidency, he served as a U.S. senator from Illinois."
    },
    "KastorScientist": {
        "repo": "Datartisan/KastorScientist",
        "id_ent": "Albert_Einstein",
        "abstract": "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity, one of the two pillars of modern physics. He was born on 14 March 1879 in Ulm, Germany. Einstein received the Nobel Prize in Physics in 1921 for his discovery of the law of the photoelectric effect. He died on 18 April 1955 in Princeton, New Jersey."
    },
    "KastorSportsTeam": {
        "repo": "Datartisan/KastorSportsTeam",
        "id_ent": "FC_Barcelona",
        "abstract": "Futbol Club Barcelona, commonly referred to as Barcelona and colloquially known as Barca, is a Spanish professional football club based in Barcelona, Catalonia, Spain. Founded in 1899 by a group of Swiss, Catalan, German and English footballers led by Joan Gamper, the club has become a symbol of Catalan culture and Catalanism."
    },
    "KastorUniversity": {
        "repo": "Datartisan/KastorUniversity",
        "id_ent": "Harvard_University",
        "abstract": "Harvard University is a private Ivy League research university in Cambridge, Massachusetts. Founded in 1636 as Harvard College, it is the oldest institution of higher learning in the United States. Harvard is named after its first benefactor, the Puritan clergyman John Harvard. The university comprises ten academic faculties plus Harvard Radcliffe Institute."
    },
    "KastorWrittenWork": {
        "repo": "Datartisan/KastorWrittenWork",
        "id_ent": "Harry_Potter_and_the_Philosopher's_Stone",
        "abstract": "Harry Potter and the Philosopher's Stone is a fantasy novel written by British author J. K. Rowling. The first novel in the Harry Potter series, it follows Harry Potter, a young wizard who discovers his magical heritage on his eleventh birthday. The book was first published on 26 June 1997 by Bloomsbury in London."
    }
}


def clean_decoded(text):
    """Clean the decoded output to fix tokenization artifacts."""
    clean = text.replace("<s>", "").replace("</s>", "").replace("<pad>", "")
    clean = clean.replace('=" ', '="').replace(" : ", ":").replace(" :", ":").replace(": ", ":")
    clean = clean.replace(' #', '#').replace("< ", "<").replace("</ ", "</")
    clean = clean.replace("= ", "=").replace('<? ', '<?').replace('# ', '#')
    clean = clean.replace(' >', '>').replace(" <", "<").replace(' =', '=')
    clean = clean.replace('/ ', '/').replace(' "/>', '"/>').replace(' ">', '">')
    clean = clean.replace(":<", ": <").replace(" ^", "^").replace("^ ", "^")
    clean = clean.replace("><", "> <")
    return clean.strip()


def load_model_and_tokenizer(model_repo, device=None):
    """
    Load a Kastor model and tokenizer from HuggingFace.

    Args:
        model_repo: HuggingFace repo ID (e.g., "Datartisan/KastorScientist")
        device: torch device (cuda/cpu/mps). If None, auto-detects.

    Returns:
        model, tokenizer
    """
    if device is None:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

    # Download checkpoint from HuggingFace
    print(f"  Downloading checkpoint from https://huggingface.co/{model_repo} ...")
    loaded=False
    for CHECKPOINT_NAME in CHECKPOINT_NAMES:
        if loaded == False:
            try:
                checkpoint_path = hf_hub_download(
                    repo_id=model_repo,
                    filename=CHECKPOINT_NAME
                )
                loaded= True
            except:
                loaded= False

    # Load tokenizer directly from HuggingFace
    print(f"  Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_repo)

    # Load the checkpoint
    print(f"  Loading checkpoint weights...")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    # Extract the model state dict from the Lightning checkpoint
    state_dict = checkpoint.get("state_dict", checkpoint)

    # Remove the 'model.' prefix from state dict keys (Lightning wraps the model)
    new_state_dict = {}
    for key, value in state_dict.items():
        if key.startswith("model."):
            new_key = key[6:]  # Remove 'model.' prefix
            new_state_dict[new_key] = value
        else:
            new_state_dict[key] = value

    # Load BART base model and then load the fine-tuned weights
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-base")

    # Resize token embeddings if tokenizer has additional tokens
    model.resize_token_embeddings(len(tokenizer))

    # Load the fine-tuned weights
    model.load_state_dict(new_state_dict, strict=False)
    model.to(device)
    model.eval()

    return model, tokenizer


def extract_triples(text, model, tokenizer, gen_kwargs=None):
    """
    Extract RDF triples from text.

    Args:
        text: Input text (e.g., biography of a scientist)
        model: The loaded Kastor model
        tokenizer: The tokenizer
        gen_kwargs: Generation kwargs (optional)

    Returns:
        List of decoded predictions (RDF triples in Turtle format)
    """
    if gen_kwargs is None:
        gen_kwargs = {
            "max_length": 256,
            "length_penalty": 0,
            "num_beams": 3,
            "num_return_sequences": 1,
            "early_stopping": False,
            "no_repeat_ngram_size": 0,
        }

    # Tokenize input
    model_inputs = tokenizer(
        text,
        max_length=256,
        padding=True,
        truncation=True,
        return_tensors='pt'
    )

    # Move to model device
    device = next(model.parameters()).device
    input_ids = model_inputs["input_ids"].to(device)
    attention_mask = model_inputs["attention_mask"].to(device)

    # Generate
    with torch.no_grad():
        generated_tokens = model.generate(
            input_ids,
            attention_mask=attention_mask,
            **gen_kwargs,
        )

    # Decode
    decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

    # Clean the output
    cleaned_preds = [clean_decoded(pred) for pred in decoded_preds]
    print(cleaned_preds)
    return cleaned_preds


def run_all_models(output_file="kastor_results.json"):
    """
    Run all Kastor models on their respective sample abstracts and save results.

    Args:
        output_file: Path to output JSON file
    """
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_models": len(KASTOR_MODELS),
            "source": "https://huggingface.co/Datartisan/models"
        },
        "results": []
    }

    print(f"\n{'='*70}")
    print(f"Running {len(KASTOR_MODELS)} Kastor models")
    print(f"{'='*70}\n")

    for idx, (model_name, config) in enumerate(KASTOR_MODELS.items(), 1):
        print(f"\n[{idx}/{len(KASTOR_MODELS)}] Processing {model_name}...")
        print("-" * 50)

        try:
            # Load model
            model, tokenizer = load_model_and_tokenizer(config["repo"])

            # Prepare input
            id_ent = config["id_ent"]
            abstract = config["abstract"]
            input_text = f"{id_ent} : {abstract}"

            # Extract triples
            print(f"  Extracting triples for {id_ent}...")
            predictions = extract_triples(input_text, model, tokenizer)

            # Store result
            result = {
                "model_name": model_name,
                "repo": config["repo"],
                "id_ent": id_ent,
                "abstract": abstract,
                "input_text": input_text,
                "predictions": predictions,
                "status": "success"
            }

            print(f"  Prediction: {predictions[0][:100]}..." if predictions else "  No prediction")

            # Free memory
            del model
            del tokenizer
            torch.cuda.empty_cache() if torch.cuda.is_available() else None

        except Exception as e:
            result = {
                "model_name": model_name,
                "repo": config["repo"],
                "id_ent": config["id_ent"],
                "abstract": config["abstract"],
                "predictions": [],
                "status": "error",
                "error": str(e)
            }
            print(f"  ERROR: {e}")

        results["results"].append(result)

    # Save results to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")

    # Summary
    successful = sum(1 for r in results["results"] if r["status"] == "success")
    print(f"\nSummary: {successful}/{len(KASTOR_MODELS)} models completed successfully")

    return results


if __name__ == "__main__":
    import os

    # Output file in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "kastor_results.json")

    results = run_all_models(output_file)
