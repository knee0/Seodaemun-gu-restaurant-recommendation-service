import A_split_sentences as step1
import B_add_aspects as step2
import C_detect_sentiments as step3
import D_calc_scores as step4
import E_show_visuals as step5

def run_pipeline():
    print("--- Start ABSA Pipeline ---")

    print("1/5: Splitting sentences...")
    step1.main()

    print("2/5: Tagging aspects...")
    step2.main()

    print("3/5: Detecting sentiment...")
    step3.main()

    print("4/5: Calculating final scores...")
    step4.main()

    print("5/5: Creating visuals...")
    step5.main()
    
    print("--- All Done. ---")

if __name__ == "__main__":
    run_pipeline()
